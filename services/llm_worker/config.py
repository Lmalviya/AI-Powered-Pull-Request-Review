import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Git Provider Config
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    GITHUB_BASE_URL: str = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
    GITLAB_BASE_URL: str = os.getenv("GITLAB_BASE_URL", "https://gitlab.com/api/v4")
    
    # Redis Config
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    ORCHESTRATOR_QUEUE: str = "orchestrator_queue"
    LLM_QUEUE: str = "llm_queue"
    GIT_QUEUE: str = "git_queue"
    
    # LLM Provider selection (auto-detected if not specified)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")
    
    # OpenAI Config
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
    
    # Ollama Config
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # Anthropic Config
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    ANTHROPIC_BASE_URL: str = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")
    
    # Prompt Config
    SYSTEM_PROMPT_NAME: str = os.getenv("SYSTEM_PROMPT_NAME", "performance")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Auto-detect provider if not explicitly set
        if not self.LLM_PROVIDER:
            if self.OPENAI_API_KEY:
                self.LLM_PROVIDER = "openai"
            elif self.ANTHROPIC_API_KEY:
                self.LLM_PROVIDER = "anthropic"
            else:
                self.LLM_PROVIDER = "ollama"

        if self.GITHUB_BASE_URL:
            self.GITHUB_BASE_URL = self.GITHUB_BASE_URL.rstrip('/')
        if self.GITLAB_BASE_URL:
            self.GITLAB_BASE_URL = self.GITLAB_BASE_URL.rstrip('/')
        if self.ANTHROPIC_BASE_URL:
            self.ANTHROPIC_BASE_URL = self.ANTHROPIC_BASE_URL.rstrip('/')

settings = Settings()