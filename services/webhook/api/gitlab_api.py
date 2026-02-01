from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from handler.gitlab_handler import GitLabEventHandler
from utils import logger, log_execution_time

router = APIRouter(prefix="/webhook")

@router.post("/gitlab")
@log_execution_time
async def gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(...),
    x_gitlab_event_uuid: str = Header(...),
    x_gitlab_token: Optional[str] = Header(None)
):
    """
    Endpoint for GitLab webhooks.
    Validates token and dispatches events to the handler.
    """
    # 1. Validate Authentication (Token)
    if not GitLabEventHandler.verify_token(x_gitlab_token):
        logger.warning(f"Invalid GitLab token received for delivery {x_gitlab_event_uuid}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # 2. Parse Payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON payload for delivery {x_gitlab_event_uuid}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. Handle Event
    await GitLabEventHandler.handle_event(x_gitlab_event, payload, x_gitlab_event_uuid)

    # 4. Acknowledge Receipt
    return {"status": "success", "message": "Event received"}
