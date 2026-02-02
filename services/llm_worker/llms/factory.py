from .open_ai_client import OpenAILLM
from .ollama_client import OllamaLLM
from ..config import settings

def get_llm_client():
    llm_provider = getattr(settings, "LLM_PROVIDER", "openai").lower()
    
    if llm_provider == "ollama":
        return OllamaLLM()
    elif llm_provider == "openai":
        return OpenAILLM()
    elif llm_provider == "anthropic":
        return AnthropicLLM()
    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")
