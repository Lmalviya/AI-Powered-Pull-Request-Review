import requests
import logging
import os
import base64
from typing import List, Dict, Any
from ..config import settings
from .base_ops import BaseOps

logger = logging.getLogger(__name__)

class GitlabOps(BaseOps):
    def __init__(self):
        self.base_url = settings.GITLAB_BASE_URL
        self.headers = {
            "PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN", "")
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            if response.status_code not in (200, 201):
                logger.error(f"GitLab API Error [{response.status_code}]: {response.text}")
                response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.exception(f"Request to GitLab failed: {e}")
            raise RuntimeError(f"Failed to communicate with GitLab: {str(e)}")

    def post_pr_comment(self, repo_id: str, pr_id: int, commit_sha: str, file: str, line: int, body: str) -> bool:
        """
        Post a comment on a specific line of a Merge Request.
        Note: Simple version using commit comments associated with the MR.
        For full MR discussions, more complex position data is required.
        """
        endpoint = f"projects/{repo_id}/merge_requests/{pr_id}/discussions"
        # Simplest form of position for GitLab
        data = {
            "body": body,
            "position": {
                "base_sha": commit_sha, # This might need to be the actual base
                "head_sha": commit_sha,
                "start_sha": commit_sha,
                "new_path": file,
                "new_line": line,
                "position_type": "text"
            }
        }
        self._request("POST", endpoint, json=data)
        return True
    
