import re
from typing import Any, AsyncGenerator

import streamlit as st


class ConversationService:
    def __init__(self, client: Any):
        self.client = client

    async def generate_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Generates a response from the client as an asynchronous stream.
        """
        async for chunk in self.client.generate(user_message):
            yield chunk

    async def generate_response_once(self, user_message: str) -> str:
        """
        Generates a complete response from the client at once.
        """
        return await self.client.generate_once(user_message)

    def should_start_ai_thinking(self, messages: list, is_ai_thinking: bool) -> bool:
        """
        Check if AI thinking should be started based on the provided state.
        """
        return (
            len(messages) > 0 and messages[-1]["role"] == "user" and not is_ai_thinking
        )

    def extract_think_content(self, text: str) -> tuple[str, str]:
        """
        Extract think content from text and return (thinking_content, remaining_text).

        Args:
            text: Input text that may contain <think> tags

        Returns:
            tuple of (thinking_content, text_without_think_tags)
        """
        # Pattern to match think tags and their content
        think_pattern = r"<think>(.*?)</think>"

        # Find all think content
        think_matches = re.findall(think_pattern, text, re.DOTALL)
        thinking_content = "\n".join(think_matches).strip()

        # Remove think tags from the original text
        cleaned_text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

        return thinking_content, cleaned_text

    def limit_messages(self, max_messages=10):
        """
        Limit the number of messages in session state.
        """
        if len(st.session_state.messages) > max_messages:
            st.session_state.messages = st.session_state.messages[-max_messages:]
