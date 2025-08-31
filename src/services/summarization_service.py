import logging
from src.protocols.ollama_client_protocol import OllamaClientProtocol

logger = logging.getLogger(__name__)


class SummarizationServiceError(Exception):
    """A custom exception for errors during the summarization process."""
    pass


class SummarizationService:
    """
    A service for summarizing web page content.
    """

    def __init__(self, llm_client: OllamaClientProtocol):
        self.llm_client = llm_client

    async def summarize(self, text: str, max_chars: int = 10000) -> str:
        """
        Summarizes the given text using the LLM API.

        Args:
            text: The text content to summarize.
            max_chars: The maximum number of characters of the text to use.

        Returns:
            The summarized text.

        Raises:
            SummarizationServiceError: If the summarization fails.
        """
        if not text or not text.strip():
            return ""

        truncated_text = text[:max_chars]
        prompt = self._build_prompt(truncated_text)

        try:
            # Collect all chunks from the async generator
            summary_parts = []
            async for chunk in self.llm_client.generate(prompt):
                summary_parts.append(chunk)
            summary = "".join(summary_parts)
            return summary.strip()
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise SummarizationServiceError(
                "要約の生成に失敗しました。外部APIとの通信中にエラーが発生しました。"
            ) from e

    def _build_prompt(self, text: str) -> str:
        """Constructs the prompt for the summarization task."""
        return f"""以下のテキストを日本語で要約してください。

テキスト:
{text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""