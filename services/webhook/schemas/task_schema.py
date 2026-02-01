from pydantic import BaseModel
from typing import Literal

class StartPRReviewTask(BaseModel):
    task_type: str = "START_PR_REVIEW"
    review_request_id: str
    provider: Literal["github", "gitlab"]
    repo: str
    pr_number: int
    delivery_id: str
