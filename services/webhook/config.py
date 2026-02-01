import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    gitlab_webhook_secret: str = os.getenv("GITLAB_WEBHOOK_SECRET", "")
    
    github_base_url: str = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
    gitlab_base_url: str = os.getenv("GITLAB_BASE_URL", "https://gitlab.com")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.github_webhook_secret and not self.gitlab_webhook_secret:
            raise ValueError("At least one of GITHUB_WEBHOOK_SECRET or GITLAB_WEBHOOK_SECRET must be set")
        self.github_base_url = self.github_base_url.rstrip('/')
        self.gitlab_base_url = self.gitlab_base_url.rstrip('/')

settings = Settings()