import requests
from typing import List, Dict
from ..config import settings
from .base_client import LLMClient

class AnthropicLLM(LLMClient):
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL
        self.api_url = settings.ANTHROPIC_BASE_URL

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise RuntimeError("Anthropic API key not configured")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Extract system prompt if present, as Anthropic handles it separately
        system_prompt = None
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        data = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": filtered_messages
        }
        
        if system_prompt:
            data["system"] = system_prompt

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            if response.status_code != 200:
                raise RuntimeError(f"Anthropic API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result["content"][0]["text"]
            
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Anthropic: {str(e)}")
