from abc import ABC, abstractmethod
from typing import List, Dict

class LLMClient(ABC):
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a text response for the given list of messages.
        Messages should be in the format: [{"role": "user/system", "content": "..."}]
        """
        pass
