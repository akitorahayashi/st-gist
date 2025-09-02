import logging
import re

from src.protocols.clients.ollama_client_protocol import OllamaClientProtocol
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
        prompt = self._build_prompt(truncated_content)

        stream_parts = []
        final_response = ""

        try:
            async for chunk in self.llm_client.generate(prompt):
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

    def _build_prompt(self, text: str) -> str:
        """Constructs the prompt for the summarization task."""
        return f"""以下のテキストを日本語で要約してください。

テキスト:
{text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""
