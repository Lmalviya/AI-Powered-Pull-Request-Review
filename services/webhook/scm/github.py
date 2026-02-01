import requests
from fastapi import HTTPException
from ..config import settings
from .base import BaseScm

class GitHubSCM(BaseScm):
    """
    GitHub implementation of the SCM interface.
    Handles GitHub-specific operations.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.github_base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Pull-Request-Pilot"
        }

    def request(self, method: str, endpoint: str, accept: str = None, **kwargs) -> requests.Response:
        """
        Internal helper for making GitHub API requests.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.headers.copy()
        if accept:
            headers["Accept"] = accept
            
        try:
            response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            
            # Diagnostic for debugging token permissions if needed
            scopes = response.headers.get("X-OAuth-Scopes")
            if scopes:
                logger.debug(f"GitHub Token Scopes: {scopes}")
                
            if response.status_code not in (200, 201):
                logger.error(f"GitHub API Error [{response.status_code}]: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"GitHub API error: {response.text}"
                )
            return response
        except requests.RequestException as e:
            logger.exception(f"Request to GitHub failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to communicate with GitHub: {str(e)}")