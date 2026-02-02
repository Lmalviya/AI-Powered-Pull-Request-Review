import requests
import logging
import os
from typing import List, Dict, Any
from ..config import settings
from .base_ops import BaseOps

logger = logging.getLogger(__name__)

class GithubOps(BaseOps):
    def __init__(self):
        self.base_url = settings.GITHUB_BASE_URL

        self.headers = {
            "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _request(self, method: str, endpoint: str, accept: str = None, **kwargs) -> requests.Response:
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
                raise RuntimeError(
                    f"GitHub API error: [{response.status_code}] {response.text}"
                )
            return response
        except requests.RequestException as e:
            logger.exception(f"Request to GitHub failed: {e}")
            raise RuntimeError(f"Failed to communicate with GitHub: {str(e)}")

    def post_pr_comment(self, repo_id: str, pr_id: int, commit_sha: str, file: str, line: int, body: str) -> bool:
        """
        Post a comment on a specific line of a Pull Request.
        """
        data = {
            "body": body,
            "commit_id": commit_sha,
            "path": file,
            "line": line,
            "side": "RIGHT"
        }
        self._request("POST", f"repos/{repo_id}/pulls/{pr_id}/comments", json=data)
        return True

