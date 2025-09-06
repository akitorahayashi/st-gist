import logging
import os
import re
from string import Template

from sdk.olm_api_client import OllamaClientProtocol

from src.protocols.models.summarization_model_protocol import SummarizationModelProtocol

logger = logging.getLogger(__name__)


class SummarizationModelError(Exception):
    """A custom exception for errors during the summarization process."""

    pass


class SummarizationModel(SummarizationModelProtocol):
    """
    A model for summarizing web page content.
    """

    def __init__(self, llm_client: OllamaClientProtocol):
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
            max_chars = int(os.getenv("MAX_PROMPT_LENGTH", "4000"))
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

    def extract_think_content(self, text: str) -> tuple[str, str]:
        """
        Extract think content from text and return (thinking_content, remaining_text).
        Handles both complete and incomplete <think> tags during streaming.

        Args:
            text: Input text that may contain <think> tags

        Returns:
            tuple of (thinking_content, text_without_think_tags)
        """
        # Pattern to match complete think tags
        complete_think_pattern = r"<think>(.*?)</think>"

        # Find all complete think content
        complete_matches = re.findall(complete_think_pattern, text, re.DOTALL)
        thinking_content = "\n".join(complete_matches).strip()

        # Check for incomplete <think> tag (started but not closed)
        incomplete_think_match = re.search(
            r"<think>((?:(?!</think>).)*?)$", text, re.DOTALL
        )
        if incomplete_think_match:
            incomplete_content = incomplete_think_match.group(1).strip()
            if incomplete_content:
                if thinking_content:
                    thinking_content += "\n" + incomplete_content
                else:
                    thinking_content = incomplete_content

        # Remove complete think tags from the original text
        cleaned_text = re.sub(complete_think_pattern, "", text, flags=re.DOTALL)

        # Remove incomplete think tag (from <think> to end of text)
        cleaned_text = re.sub(
            r"<think>(?:(?!</think>).)*?$", "", cleaned_text, flags=re.DOTALL
        )

        cleaned_text = cleaned_text.strip()

        return thinking_content, cleaned_text

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

        stream_parts = []
        final_response = ""

        try:
            summary_model = os.getenv("SUMMARY_MODEL", "qwen3:0.6b")
            async for chunk in self.llm_client.gen_stream(
                truncated_prompt, model=summary_model
            ):
                stream_parts.append(chunk)
                current_response = "".join(stream_parts)
                thinking_content, summary_content = self.extract_think_content(
                    current_response
                )
                yield thinking_content, summary_content
            final_response = "".join(stream_parts)

        except Exception as e:
            logger.error(f"Streaming summarization failed: {e}")
            error_msg = "要約のストリーミング生成に失敗しました。"
            self.last_error = error_msg
            raise SummarizationModelError(error_msg) from e
        finally:
            self.is_summarizing = False

        # Final processing when streaming is complete
        thinking_content, summary_content = self.extract_think_content(final_response)

        # Store final results in instance variables
        self.thinking = thinking_content
        self.summary = summary_content

        yield thinking_content, summary_content

    def reset(self):
        """Reset the summarization model state."""
        self.summary = ""
        self.thinking = ""
        self.is_summarizing = False
        self.last_error = None
