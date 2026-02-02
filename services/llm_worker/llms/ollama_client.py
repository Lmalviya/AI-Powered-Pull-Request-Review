import requests
import json
from typing import List, Dict
from ..config import settings
from .base_client import LLMClient

class OllamaLLM(LLMClient):
    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama2")

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        url = f"{self.base_url}/api/chat"
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json"
        }
        try:
            response = requests.post(url, json=data, timeout=300) 
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API Error: {response.text}")
            
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Ollama: {str(e)}")