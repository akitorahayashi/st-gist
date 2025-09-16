import logging
import os
from string import Template

import streamlit as st

from src.protocols import OlmClientV2Protocol, SummarizationModelProtocol
from src.schemas import Message, MessageRole

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

        accumulated_thinking = ""
        accumulated_content = ""

        try:
            summary_model = st.secrets.get("SUMMARY_MODEL", "qwen3:0.6b")
            messages = [Message(role=MessageRole.USER, content=truncated_prompt)]
            stream = await self.llm_client.generate(
                messages=messages, model_name=summary_model, stream=True
            )
            async for chunk in stream:
                try:
                    # Handle both dict and object responses
                    if isinstance(chunk, dict):
                        choices = chunk.get("choices", [])
                    elif hasattr(chunk, "choices"):
                        choices = chunk.choices
                    else:
                        # Unexpected format - skip this chunk
                        logger.warning(f"Unexpected chunk format: {type(chunk)}")
                        continue

                    if choices and len(choices) > 0:
                        choice = choices[0]

                        # Extract delta from choice
                        if isinstance(choice, dict):
                            delta = choice.get("delta", {})
                        elif hasattr(choice, "delta"):
                            delta = choice.delta
                        else:
                            # No delta found - skip
                            continue

                        # Accumulate thinking deltas
                        if isinstance(delta, dict):
                            think_content = delta.get("think", "")
                            content = delta.get("content", "")
                        else:
                            think_content = getattr(delta, "think", "")
                            content = getattr(delta, "content", "")

                        if think_content:
                            accumulated_thinking += think_content
                        if content:
                            accumulated_content += content

                        # Yield current state
                        yield accumulated_thinking, accumulated_content

                except Exception as e:
                    logger.warning(f"Error processing chunk: {e}")
                    # Continue processing other chunks
                    continue

        except Exception as e:
            logger.error(f"Streaming summarization failed: {e}")

            # 接続エラーの場合はより具体的なメッセージを提供
            if "connection" in str(e).lower() or "failed" in str(e).lower():
                error_msg = "Ollamaサーバーへの接続に失敗しました。サーバーが起動しているか確認してください。"
            else:
                error_msg = f"要約のストリーミング生成に失敗しました: {str(e)}"

            self.last_error = error_msg
            raise SummarizationModelError(error_msg) from e
        finally:
            self.is_summarizing = False

        # Store final results in instance variables
        self.thinking = accumulated_thinking
        self.summary = accumulated_content

        # Final yield with complete data
        yield accumulated_thinking, accumulated_content

    def reset(self):
        """Reset the summarization model state."""
        self.summary = ""
        self.thinking = ""
        self.is_summarizing = False
        self.last_error = None
