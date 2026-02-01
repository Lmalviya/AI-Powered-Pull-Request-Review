from typing import Dict, Type
from ..git_operation.base_ops import BaseOps
from ..git_operation.github_ops import GithubOps
from ..git_operation.gitlab_ops import GitlabOps

class ProviderRegistry:
    """
    Central registry for SCM providers and other configurable components.
    """
    _scm_providers: Dict[str, Type[BaseOps]] = {
        "github": GithubOps,
        "gitlab": GitlabOps
    }

    @classmethod
    def get_scm_class(cls, provider_name: str) -> Type[BaseOps]:
        return cls._scm_providers.get(provider_name.lower(), GithubOps)

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseOps]):
        cls._scm_providers[name.lower()] = provider_class
