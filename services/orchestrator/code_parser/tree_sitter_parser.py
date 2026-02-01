import importlib
from tree_sitter import Parser, Language
from .language import NODE_TYPES

class UniversalParser:
    def __init__(self):
        self.parsers = {}

    def get_language(self, language_name: str):
        """Dynamically load the tree-sitter language module."""
        # Special case for TypeScript/TSX which share a package
        if language_name in ["typescript", "tsx"]:
            try:
                module = importlib.import_module("tree_sitter_typescript")
                func_name = "language_typescript" if language_name == "typescript" else "language_tsx"
                return Language(getattr(module, func_name)())
            except Exception as e:
                raise ValueError(f"Could not load tree_sitter_typescript: {e}")

        module_name = f"tree_sitter_{language_name}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "language"):
                return Language(module.language())
            raise AttributeError(f"Module {module_name} has no 'language()' function.")
        except Exception as e:
            raise ValueError(f"Could not load tree-sitter language for {language_name}: {e}")


    def get_parser(self, language_name: str):
        if language_name not in self.parsers:
            lang = self.get_language(language_name)
            self.parsers[language_name] = Parser(lang)
        return self.parsers[language_name]

    def get_semantic_tokens(self, content: str, language_name: str) -> str:
        """Extracts a normalized string of semantic tokens (ignoring comments/whitespace)."""
        try:
            parser = self.get_parser(language_name)
            tree = parser.parse(bytes(content, "utf8"))
            tokens = []
            self._walk_semantic(tree.root_node, tokens)
            return "".join(tokens)
        except Exception:
            return ""

    def _walk_semantic(self, node, tokens):
        """Recursively collects semantic tokens, ignoring comments."""
        # Tree-sitter 'extra' nodes are usually comments/whitespace
        # We also check for 'comment' in the type string for robustness
        if node.is_extra or "comment" in node.type:
            return

        if not node.children:
            text = node.text.decode("utf8").strip()
            if text:
                tokens.append(text)
            return

        for child in node.children:
            self._walk_semantic(child, tokens)

    def parse_structure(self, content: str, language_name: str) -> str:
        try:
            parser = self.get_parser(language_name)
            tree = parser.parse(bytes(content, "utf8"))
            
            results = []
            visited_lines = set() # Prevent duplicate reports for the same line
            
            self._walk(tree.root_node, language_name, results, visited_lines)
            
            # Final Sort
            results.sort(key=lambda x: int(x.split(":")[0].replace("Line ", "")))
            
            return "\n".join(results) if results else "No classes or functions found."
        except Exception as e:
            return f"Error parsing {language_name} file structure: {str(e)}"

    def _walk(self, node, lang, results, visited_lines):
        node_type = node.type
        mapping = NODE_TYPES.get(lang, {})
        
        if node_type in mapping:
            line_no = node.start_point[0] + 1
            
            # Only report the FIRST thing found on a specific line to avoid duplicates
            if line_no not in visited_lines:
                label = mapping[node_type]
                name = self._extract_name(node)
                results.append(f"Line {line_no}: {label} {name}")
                visited_lines.add(line_no)
        
        # Always recurse
        for child in node.children:
            self._walk(child, lang, results, visited_lines)

    def _extract_name(self, node):
        """Finds the most logical identifier for a definition node."""
        # Generic name-holding child types across many grammars
        name_types = {"identifier", "type_identifier", "field_identifier", "property_identifier", "constant", "name"}
        
        # 1. Look for direct children first (standard case)
        for child in node.children:
            if child.type in name_types:
                return child.text.decode("utf8")
        
        # 2. Look one level deeper (for Go type_spec or C++ complex declarators)
        for child in node.children:
            for grandchild in child.children:
                if grandchild.type in name_types:
                    return grandchild.text.decode("utf8")
                    
        return "unknown"

    def extract_function_content(self, content: str, language_name: str, target_name: str) -> str:
        """Finds the content of a function or class by its name."""
        try:
            parser = self.get_parser(language_name)
            tree = parser.parse(bytes(content, "utf8"))
            
            node = self._find_node_by_name(tree.root_node, language_name, target_name)
            if node:
                return node.text.decode("utf8")
            return f"Could not find function/class '{target_name}' in the provided content."
        except Exception as e:
            return f"Error extracting function content: {str(e)}"

    def _find_node_by_name(self, node, lang, target_name):
        node_type = node.type
        mapping = NODE_TYPES.get(lang, {})
        
        if node_type in mapping:
            name = self._extract_name(node)
            if name == target_name:
                return node
        
        for child in node.children:
            result = self._find_node_by_name(child, lang, target_name)
            if result:
                return result
        return None
