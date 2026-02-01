from pydantic import BaseModel
from typing import Optional

class GitHubUser(BaseModel):
    login: str

class PullRequest(BaseModel):
    title: str
    number: int
    user: GitHubUser
    base: dict
    head: dict

class Repository(BaseModel):
    full_name: str
    owner: GitHubUser

class PullRequestEvent(BaseModel):
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository
    sender: GitHubUser