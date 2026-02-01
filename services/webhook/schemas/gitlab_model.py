from pydantic import BaseModel, Field
from typing import Optional, List

class GitLabUser(BaseModel):
    name: str
    username: str
    avatar_url: Optional[str] = None

class Project(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    web_url: str
    path_with_namespace: str

class ObjectAttributes(BaseModel):
    id: int
    iid: int  # This is the "Merge Request Number"
    target_branch: str
    source_branch: str
    title: str
    state: str
    action: str  # open, close, update, reopen
    url: str
    last_commit: dict = Field(..., alias="last_commit")

class MergeRequestEvent(BaseModel):
    object_kind: str = "merge_request"
    user: GitLabUser
    project: Project
    object_attributes: ObjectAttributes
    repository: dict
