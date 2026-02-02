import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GITHUB_BASE_URL: str = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
    GITLAB_BASE_URL: str = os.getenv("GITLAB_BASE_URL", "https://gitlab.com/api/v4")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    ORCHESTRATOR_QUEUE: str = "orchestrator_queue"
    LLM_QUEUE: str = "llm_queue"
    GIT_QUEUE: str = "git_queue"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.GITHUB_BASE_URL:
            self.GITHUB_BASE_URL = self.GITHUB_BASE_URL.rstrip('/')
        if self.GITLAB_BASE_URL:
            self.GITLAB_BASE_URL = self.GITLAB_BASE_URL.rstrip('/')

settings = Settings()