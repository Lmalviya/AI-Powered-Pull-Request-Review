
import logging
from ..code_parser.tree_sitter_parser import UniversalParser

logger = logging.getLogger(__name__)

class SemanticFilter:
    """
    Service to determine if changes in a file are semantically meaningful
    or just noise (comments, whitespace, etc.).
    """
    def __init__(self):
        self.parser = UniversalParser()

    def is_semantic_change(self, old_content: str, new_content: str, filename: str) -> bool:
        """
        Returns True if the change between old and new content is semantic.
        Returns False if it's only comments or whitespace.
        """
        language = self._get_language_from_filename(filename)
        if not language:
            # If we don't support the language, assume it's semantic to be safe
            return True
            
        old_tokens = self.parser.get_semantic_tokens(old_content, language)
        new_tokens = self.parser.get_semantic_tokens(new_content, language)
        
        # If both fail to parse (empty tokens), we can't be sure, so assume semantic
        if not old_tokens and not new_tokens and old_content.strip() != new_content.strip():
            return True
            
        return old_tokens != new_tokens

    def _get_language_from_filename(self, filename: str) -> str:
        """Maps file extensions to tree-sitter language names."""
        ext = filename.split('.')[-1].lower()
        mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'tsx': 'tsx',
            'go': 'go',
            'java': 'java',
            'rs': 'rust',
            'cpp': 'cpp',
            'cc': 'cpp',
            'c': 'c',
            'rb': 'ruby'
        }
        return mapping.get(ext)
