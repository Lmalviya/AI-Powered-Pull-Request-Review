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

    def get_pull_request(self, repo_id: str, pr_id: int) -> dict:
        """
        Fetch the pull request metadata.
        """
        response = self._request("GET", f"repos/{repo_id}/pulls/{pr_id}")
        return response.json()

    def get_pull_request_file_diffs(self, repo_id: str, pr_id: int) -> List[Dict[str, Any]]:
        """
        Fetch the list of files changed in a PR with their patches.
        """
        response = self._request("GET", f"repos/{repo_id}/pulls/{pr_id}/files")
        return response.json()

    def get_file_content(self, repo_id: str, file_path: str, ref: str = None) -> str:
        """
        Fetch the content of a specific file.
        """
        endpoint = f"repos/{repo_id}/contents/{file_path.lstrip('/')}"
        params = {"ref": ref} if ref else {}
        response = self._request("GET", endpoint, params=params)
        
        # GitHub returns base64 encoded content for this endpoint
        import base64
        data = response.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        return content


