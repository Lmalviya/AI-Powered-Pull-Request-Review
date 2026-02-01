import hmac
import hashlib
from fastapi import HTTPException
from ..config import settings
from ..schemas.github_model import PullRequestEvent
from ..schemas.task_schema import StartPRReviewTask
from ..utils import logger, log_execution_time, generate_id

class GitHubEventHandler:
    """
    Handles GitHub webhook events and dispatches them to the appropriate services.
    """
    
    @staticmethod
    def verify_signature(body: bytes, signature_header: str) -> bool:
        """
        Verify that the webhook signature matches the expected signature 
        calculated using the secret.
        """
        if not settings.github_webhook_secret:
            logger.error("GITHUB_WEBHOOK_SECRET is not configured in settings")
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
            key=settings.github_webhook_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_signature, computed_signature)

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
            review_request_id=review_request_id,
            provider="github",
            repo=pr_event.repository.full_name,
            pr_number=pr_event.number,
            delivery_id=delivery_id
        )

        # TODO: Actually push 'task.dict()' to the orchestrator_queue via Redis/RabbitMQ
        logger.info(f"TASK ENQUEUED: START_PR_REVIEW | RequestID: {review_request_id} | Repo: {task.repo} | PR: #{task.pr_number}")
        return review_request_id