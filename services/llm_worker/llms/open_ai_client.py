import requests
from typing import List, Dict
from ..config import settings
from .base_client import LLMClient

class OpenAILLM(LLMClient):
    def __init__(self):
        self.api_key = getattr(settings, "OPENAI_API_KEY", None)
        self.model = getattr(settings, "OPENAI_MODEL", "gpt-4")
        self.api_url = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1, # Set low for more deterministic reviews
            "response_format": { "type": "json_object" }
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            if response.status_code != 200:
                raise RuntimeError(f"OpenAI API Error: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with OpenAI: {str(e)}")
