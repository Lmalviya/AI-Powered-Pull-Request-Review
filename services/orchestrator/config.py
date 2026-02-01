import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_HUNK_CHANGES: int = 10
    IGNORED_EXTENSIONS: str = ".lock,.json,.map,.svg,.png,.jpg,.jpeg,.pyc,.yml,.toml,.pyd,.md,.dockerignore"
    IGNORED_FILES: str = ".gitignore,.env,LICENSE,CONTRIBUTING.md"
    IGNORED_DIRECTORIES: str = "__pycache__,node_modules,.venv,tests,migrations"
    GITHUB_BASE_URL: str = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
    GITLAB_BASE_URL: str = os.getenv("GITLAB_BASE_URL", "https://gitlab.com/api/v4")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
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