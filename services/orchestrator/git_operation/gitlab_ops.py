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

    def get_pull_request(self, repo_id: str, pr_id: int) -> dict:
        endpoint = f"projects/{repo_id}/merge_requests/{pr_id}"
        response = self._request("GET", endpoint)
        data = response.json()
        # Normalize to look like GitHub if possible, or handle difference in workflow
        # For now just return the data, mainly needed for sha/ref
        return {
            "base": {"sha": data.get("diff_refs", {}).get("base_sha")},
            "head": {"sha": data.get("diff_refs", {}).get("head_sha")},
            # Map other fields if necessary
        }

    def get_pull_request_file_diffs(self, repo_id: str, pr_id: int) -> List[Dict[str, Any]]:
        endpoint = f"projects/{repo_id}/merge_requests/{pr_id}/changes"
        response = self._request("GET", endpoint)
        changes = response.json().get("changes", [])
        
        # Normalize to internal format
        results = []
        for c in changes:
            results.append({
                "filename": c.get("new_path"),
                "patch": c.get("diff")
            })
        return results

    def get_pull_request_comments(self, repo_id: str, pr_id: int) -> List[Dict[str, Any]]:
        endpoint = f"projects/{repo_id}/merge_requests/{pr_id}/notes"
        response = self._request("GET", endpoint)
        return response.json()

    def get_file_content(self, repo_id: str, file_path: str, ref: str = None) -> str:
        import urllib.parse
        safe_path = urllib.parse.quote(file_path, safe='')
        endpoint = f"projects/{repo_id}/repository/files/{safe_path}/raw"
        params = {"ref": ref} if ref else {}
        response = self._request("GET", endpoint, params=params)
        return response.text
