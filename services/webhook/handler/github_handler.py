import hmac
import hashlib
from fastapi import HTTPException
from ..config import settings
from ..schemas.github_model import PullRequestEvent
from ..schemas.task_schema import StartPRReviewTask
from ..utils import logger, log_execution_time, generate_id
from ..queue_manager import queue_manager

class GitHubEventHandler:
    """
    Handles GitHub webhook events and dispatches them to the appropriate services.
    """
    
    @staticmethod
    def verify_signature(body: bytes, signature_header: str) -> bool:
        """
        Verify that the webhook signature matches the expected signature 
        """
        if not settings.github_token:
            logger.error("GITHUB_TOKEN is not configured in settings")
            raise HTTPException(status_code=500, detail="Server configuration error")

        if not signature_header:
            logger.warning("Missing x-hub-signature-256 header")
            return False
        
        expected_prefix = "sha256="
        if not signature_header.startswith(expected_prefix):
            logger.warning("Invalid signature prefix")
            return False
        
        received_signature = signature_header[len(expected_prefix):]
        computed_signature = hmac.new(
            key=settings.github_token.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(received_signature, computed_signature):
            logger.warning(f"Signature Mismatch! Received: {received_signature} | Computed: {computed_signature} | Secret Len: {len(settings.github_webhook_secret)}")
            return False

        return True

    @classmethod
    @log_execution_time
    async def handle_event(cls, event_type: str, payload: dict, delivery_id: str):
        """
        Dispatch GitHub webhook events to the appropriate handlers.
        """
        logger.info(f"Processing GitHub event: {event_type} (Delivery: {delivery_id})")

        if event_type == "pull_request":
            pr_event = PullRequestEvent(**payload)
            
            # INTERESTING ACTIONS: New PR or New Commits (synchronize)
            if pr_event.action in ["opened", "synchronize", "reopened"]:
                logger.info(f"Target action detected: {pr_event.action} for PR #{pr_event.number}")
                await cls.enqueue_task(pr_event, delivery_id)
            else:
                logger.info(f"Ignoring action: {pr_event.action} for PR #{pr_event.number}")
        else:
            logger.info(f"Ignoring unhandled event type: {event_type}")

    @staticmethod
    async def enqueue_task(pr_event: PullRequestEvent, delivery_id: str):
        """
        Push the task into the queue for processing.
        """
        review_request_id = generate_id()
        
        task = StartPRReviewTask(
            action="START_PR_REVIEW",
            review_request_id=review_request_id,
            provider="github",
            repo=pr_event.repository.full_name,
            pr_number=pr_event.number,
            delivery_id=delivery_id
        )

        # Push to the orchestrator_queue via Redis
        try:
            await queue_manager.enqueue(settings.orchestrator_queue, task.model_dump())
            logger.info(f"TASK ENQUEUED: START_PR_REVIEW | RequestID: {review_request_id} | Repo: {task.repo} | PR: #{task.pr_number}")
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            raise HTTPException(status_code=500, detail="Failed to enqueue task")
            
        return review_request_id