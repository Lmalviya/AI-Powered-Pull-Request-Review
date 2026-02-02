from abc import ABC, abstractmethod

class BaseOps(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def post_pr_comment(self, repo_id: str, pr_id: int, commit_sha: str, file: str, line: int, body: str) -> bool:
        """
        Post a comment on a specific line of a Pull Request / Merge Request.
        """
        raise NotImplementedError

