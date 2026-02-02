from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseOps(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_pull_request_file_diffs(self, repo_id: str, pr_id: int) -> List[Dict[str, Any]]:
        """
        Fetch the list of files changed in a PR with their patches.
        """
        raise NotImplementedError

    @abstractmethod
    def get_pull_request(self, repo_id: str, pr_id: int) -> dict:
        """
        Fetch the pull request metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_content(self, repo_id: str, file_path: str, ref: str = None) -> str:
        """
        Fetch the content of a specific file at a given ref (SHA or branch).
        """
        raise NotImplementedError

    
