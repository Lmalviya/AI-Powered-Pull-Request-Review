import re
from typing import Generator, Dict, List, Any
from ..config import settings
class HunkProcessor:
    """
    Utility to process and chunk git diff patches into smaller pieces
    while maintaining accurate line numbers for inline comments.
    """
    def __init__(self):
        self.max_changes = settings.MAX_HUNK_CHANGES

    def chunk_patch(self, filename: str, patch: str) -> Generator[Dict[str, Any], None, None]:
        """
        Parses a unified diff patch and yields chunks limited by the number of changes (+/-).
        Each chunk includes calculated line numbers for the NEW file.
        """
        if not patch:
            return

        lines = patch.splitlines()
        hunk_header_re = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')
        
        current_new_line = 0
        chunk_lines = []
        change_count = 0
        chunk_start_line = 0

        for line in lines:
            header_match = hunk_header_re.match(line)
            if header_match:
                # If we have a pending chunk from a previous hunk, yield it
                if chunk_lines:
                    yield {
                        "filename": filename,
                        "content": "\n".join(chunk_lines),
                        "start_line": chunk_start_line,
                        "end_line": current_new_line,
                        "changes": change_count
                    }
                    chunk_lines = []
                    change_count = 0

                # Initialize new hunk tracking
                # We care about the '+' part for the new file line numbers
                current_new_line = int(header_match.group(3))
                chunk_start_line = current_new_line
                chunk_lines.append(line)  # Keep the header for context
                continue

            if not chunk_lines and current_new_line == 0:
                # Skip any lines before the first hunk header
                continue

            # Process individual lines
            if line.startswith('+'):
                change_count += 1
                chunk_lines.append(f"{current_new_line}: {line}")
                current_new_line += 1
            elif line.startswith('-'):
                change_count += 1
                # Deleted lines don't exist in the new file, 
                # but we show them to the LLM for context. 
                # We don't increment current_new_line.
                chunk_lines.append(f"DEL: {line}")
            elif line.startswith(' '):
                # Context line
                chunk_lines.append(f"{current_new_line}: {line}")
                current_new_line += 1
            else:
                # Metadata or other (like \ No newline at end of file)
                chunk_lines.append(line)

            # Check if we should yield the chunk
            if change_count >= self.max_changes:
                yield {
                    "filename": filename,
                    "content": "\n".join(chunk_lines),
                    "start_line": chunk_start_line,
                    "end_line": current_new_line - 1 if current_new_line > chunk_start_line else chunk_start_line,
                    "changes": change_count
                }
                # Prepare for next chunk
                chunk_lines = [f"@@ ... @@ (Continued focus on {filename})"]
                chunk_start_line = current_new_line
                change_count = 0

        # Yield last chunk
        if chunk_lines and change_count > 0:
            yield {
                "filename": filename,
                "content": "\n".join(chunk_lines),
                "start_line": chunk_start_line,
                "end_line": current_new_line - 1 if current_new_line > chunk_start_line else chunk_start_line,
                "changes": change_count
            }
