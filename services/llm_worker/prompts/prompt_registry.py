from .reviewer_prompt import PERFORMANCE_FOCUSED_PROMPT
from ..config import settings

PROMPT_REGISTRY = {
    "performance": PERFORMANCE_FOCUSED_PROMPT
}

def get_system_prompt(**kwargs) -> str:
    # Use config if available, otherwise default to performance
    system_prompt_name = getattr(settings, "SYSTEM_PROMPT_NAME", "performance")
    
    if system_prompt_name not in PROMPT_REGISTRY:
        system_prompt_name = "performance"
    
    prompt_template = PROMPT_REGISTRY.get(system_prompt_name)
    
    # Default values for common keys if not provided
    defaults = {
        "previous_feedback": "None"
    }
    defaults.update(kwargs)
    
    return prompt_template.format(**defaults)