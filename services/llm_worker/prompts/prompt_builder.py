from .prompt_registry import get_system_prompt

class PromptBuilder:
    def build_initial_messages(self, chunk: dict, repo_id: str, pr_id: str) -> list:
        # 1. Get System Prompt
        system_prompt = get_system_prompt()
        
        # 2. Build User Message
        user_message = (
            f"Repository ID: {repo_id}\n"
            f"PR ID: {pr_id}\n"
            f"File: {chunk.get('filename')}\n"
            f"Diff Highlights:\n"
            f"{chunk.get('diff_snippet')}\n\n"
            f"Review the code above. If you need more context, use a tool. Otherwise, provide inline comments."
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

    def build_context_message(self, context_data: dict) -> dict:
        # This is used when the git worker returns with additional context
        tool_name = context_data.get("tool")
        content = context_data.get("content")
        
        msg = f"Additional Context for tool '{tool_name}':\n\n{content}\n\n"
        msg += "Based on this new information, please complete your review."
        
        return {"role": "user", "content": msg}

prompt_builder = PromptBuilder()