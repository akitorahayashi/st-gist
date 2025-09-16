import json
import logging
import os
import re
from string import Template

import streamlit as st
from olm_api.api.v2.schemas.message import Message, MessageRole
from olm_api_sdk.v2 import OlmClientV2Protocol

from src.protocols import SummarizationModelProtocol

logger = logging.getLogger(__name__)


class SummarizationModelError(Exception):
    """A custom exception for errors during the summarization process."""

    pass


class SummarizationModel(SummarizationModelProtocol):
    """
    A model for summarizing web page content.
    """

    def __init__(self, llm_client: OlmClientV2Protocol):
        self.llm_client = llm_client
        self.summary = ""
        self.thinking = ""
        self.is_summarizing = False
        self.last_error = None
        self._summarization_prompt_template = self._load_summarization_prompt_template()

    def _truncate_prompt(self, prompt: str, max_chars: int = None) -> str:
        """
        Truncate prompt from the end if it exceeds max_chars to preserve important context at the beginning.

        Args:
            prompt: The prompt to potentially truncate
            max_chars: Maximum number of characters allowed (default from MAX_PROMPT_LENGTH env var)

        Returns:
            str: Truncated prompt if necessary
        """
        if max_chars is None:
            max_chars = st.secrets.get("MAX_PROMPT_LENGTH", 4000)
        if len(prompt) <= max_chars:
            return prompt
        return prompt[:max_chars]

    def _load_summarization_prompt_template(self) -> Template:
        """
        Load the summarization prompt template from the static file.

        Returns:
            Template: The prompt template object

        Raises:
            FileNotFoundError: If the prompt template file is not found
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "prompts",
            "summarization_prompt.md",
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return Template(f.read())

    def _parse_thinking_content(self, text: str) -> tuple[str, str]:
        """
        Parse text to extract thinking and content parts.

        Args:
            text: Text potentially containing <think> tags

        Returns:
            tuple: (thinking_content, actual_content)
        """
        if not text:
            return "", ""

        # Extract complete thinking content (with both opening and closing tags)
        thinking_pattern = r"<think>(.*?)</think>"
        thinking_matches = re.findall(thinking_pattern, text, re.DOTALL)
        thinking_content = "\n".join(thinking_matches).strip()

        # Remove complete thinking tags to get actual content
        content_without_thinking = re.sub(
            thinking_pattern, "", text, flags=re.DOTALL
        )

        # Handle incomplete thinking tags at the end (streaming case)
        # Extract content from incomplete <think> tags and add to thinking_content
        incomplete_thinking_pattern = r"<think>(.*)$"
        incomplete_match = re.search(incomplete_thinking_pattern, content_without_thinking, re.DOTALL)
        if incomplete_match:
            # Add incomplete thinking content to thinking_content
            incomplete_content = incomplete_match.group(1).strip()
            if incomplete_content:
                if thinking_content:
                    thinking_content += "\n" + incomplete_content
                else:
                    thinking_content = incomplete_content

            # Remove the incomplete <think> tag and its content from actual content
            content_without_thinking = re.sub(
                incomplete_thinking_pattern, "", content_without_thinking, flags=re.DOTALL
            )

        return thinking_content, content_without_thinking.strip()

    async def stream_summary(self, scraped_content: str):
        """
        Handle stream generation from scraped content and yield thinking/summary content.

        Args:
            scraped_content: The scraped content to summarize.

        Yields:
            tuple[str, str]: (thinking_content, summary_content) for each chunk
        """
        self.is_summarizing = True
        self.last_error = None

        truncated_content = scraped_content[:10000]
        prompt = self._summarization_prompt_template.safe_substitute(
            content=truncated_content
        )

        truncated_prompt = self._truncate_prompt(prompt)

        accumulated_raw = ""

        try:
            summary_model = st.secrets.get("SUMMARY_MODEL", "qwen3:0.6b")
            messages = [Message(role=MessageRole.USER, content=truncated_prompt)]
            stream = await self.llm_client.generate(
                messages=messages, model_name=summary_model, stream=True
            )
            async for chunk in stream:
                # Parse JSON string if necessary
                if isinstance(chunk, str):
                    try:
                        chunk = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue

                choices = (
                    chunk.get("choices") if isinstance(chunk, dict) else chunk.choices
                )
                if choices and len(choices) > 0:
                    choice = choices[0]
                    delta = (
                        choice.get("delta")
                        if isinstance(choice, dict)
                        else choice.delta
                    )

                    # Accumulate all content (including think tags)
                    content = (
                        delta.get("content")
                        if isinstance(delta, dict)
                        else getattr(delta, "content", None)
                    )
                    if content:
                        accumulated_raw += content

                        # Parse to separate thinking and actual content
                        thinking_content, actual_content = self._parse_thinking_content(accumulated_raw)
                        yield thinking_content, actual_content

        except Exception as e:
            logger.error(f"Streaming summarization failed: {e}")
            error_msg = "要約のストリーミング生成に失敗しました。"
            self.last_error = error_msg
            raise SummarizationModelError(error_msg) from e
        finally:
            self.is_summarizing = False

        # Store final results in instance variables
        final_thinking, final_summary = self._parse_thinking_content(accumulated_raw)
        self.thinking = final_thinking
        self.summary = final_summary

        # Final yield with complete data
        yield final_thinking, final_summary

    def reset(self):
        """Reset the summarization model state."""
        self.summary = ""
        self.thinking = ""
        self.is_summarizing = False
        self.last_error = None
