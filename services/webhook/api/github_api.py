from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from handler.github_handler import GitHubEventHandler
from utils import logger, log_execution_time

router = APIRouter(prefix="/webhook")

@router.post("/github")
@log_execution_time
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_github_delivery: str = Header(...),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Endpoint for GitHub webhooks.
    Validates signature and dispatches events to the handler.
    """
    body = await request.body()
    
    # 1. Validate Authentication (Signature)
    if not GitHubEventHandler.verify_signature(body, x_hub_signature_256):
        logger.warning(f"Invalid webhook signature received for delivery {x_github_delivery}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse Payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON payload for delivery {x_github_delivery}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. Handle Event (validate event/action and enqueue)
    await GitHubEventHandler.handle_event(x_github_event, payload, x_github_delivery)

    # 4. Acknowledge Receipt
    return {"status": "success", "message": "Event received"}