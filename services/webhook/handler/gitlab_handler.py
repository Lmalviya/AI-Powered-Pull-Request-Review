from fastapi import HTTPException
from config import settings
from schemas.gitlab_model import MergeRequestEvent
from schemas.task_schema import StartPRReviewTask
from utils import logger, log_execution_time, generate_id
from queue_manager import queue_manager

class GitLabEventHandler:
    """
    Handles GitLab webhook events and dispatches them to the appropriate services.
    """
    
    @staticmethod
    def verify_token(token_header: str) -> bool:
        """
        Verify that the X-Gitlab-Token matches the configured secret.
        """
        if not settings.gitlab_webhook_secret:
            logger.error("GITLAB_WEBHOOK_SECRET is not configured in settings")
            raise HTTPException(status_code=500, detail="Server configuration error")

        if not token_header:
            logger.warning("Missing X-Gitlab-Token header")
            return False
            
        return token_header == settings.gitlab_webhook_secret

    @classmethod
    @log_execution_time
    async def handle_event(cls, event_type: str, payload: dict, delivery_id: str):
        """
        Dispatch GitLab webhook events to the appropriate handlers.
        """
        logger.info(f"Processing GitLab event: {event_type} (Delivery: {delivery_id})")

        if event_type == "Merge Request Hook":
            mr_event = MergeRequestEvent(**payload)
            action = mr_event.object_attributes.action
            iid = mr_event.object_attributes.iid
            project_path = mr_event.project.path_with_namespace
            
            # INTERESTING ACTIONS: open, update, reopen
            if action in ["open", "update", "reopen"]:
                logger.info(f"Target action detected: {action} for MR !{iid} in {project_path}")
                await cls.enqueue_task(mr_event, delivery_id)
            else:
                logger.info(f"Ignoring action: {action} for MR !{iid}")
        else:
            logger.info(f"Ignoring unhandled event type: {event_type}")

    @staticmethod
    async def enqueue_task(mr_event: MergeRequestEvent, delivery_id: str):
        """
        Push the task into the queue for processing.
        """
        review_request_id = generate_id()

        task = StartPRReviewTask(
            action="START_PR_REVIEW",
            review_request_id=review_request_id,
            provider="gitlab",
            repo=mr_event.project.path_with_namespace,
            pr_number=mr_event.object_attributes.iid,
            delivery_id=delivery_id
        )

        # Push to the orchestrator_queue via Redis
        try:
            queue_manager.enqueue(settings.orchestrator_queue, task.model_dump())
            logger.info(f"TASK ENQUEUED: START_PR_REVIEW | RequestID: {review_request_id} | Repo: {task.repo} | MR: !{task.pr_number}")
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            raise HTTPException(status_code=500, detail="Failed to enqueue task")
            
        return review_request_id
