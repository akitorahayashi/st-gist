import logging

from src.protocols.ollama_client_protocol import OllamaClientProtocol

logger = logging.getLogger(__name__)


class SummarizationModelError(Exception):
    """A custom exception for errors during the summarization process."""

    pass


class SummarizationModel:
    """
    A model for summarizing web page content.
    """

    def __init__(self, llm_client: OllamaClientProtocol):
        self.llm_client = llm_client
        self.summary = ""
        self.thinking = ""
        self.is_summarizing = False

    async def stream_summary(self, scraped_content: str):
        """
        Handle stream generation from scraped content and yield thinking/summary content.

        Args:
            scraped_content: The scraped content to summarize.

        Yields:
            tuple[str, str]: (thinking_content, summary_content) for each chunk
        """
        # Import here to avoid circular imports

        conv_s = None
        # Get conversation service from session state (needed for extract_think_content)
        import streamlit as st

        if "conversation_service" in st.session_state:
            conv_s = st.session_state.get("conversation_service")

        # Set processing state
        self.is_summarizing = True

        truncated_content = scraped_content[:10000]
        prompt = self._build_prompt(truncated_content)

        stream_parts = []

        try:
            async for chunk in self.llm_client.generate(prompt):
                stream_parts.append(chunk)

                # Process current response and extract thinking/summary content
                current_response = "".join(stream_parts)
                thinking_content, summary_content = "", ""
                last_think_start = current_response.rfind("<think>")
                last_think_end = current_response.rfind("</think>")

                if last_think_start != -1:
                    summary_before_think = current_response[:last_think_start]
                    if last_think_end > last_think_start:
                        thinking_content = current_response[
                            last_think_start + 7 : last_think_end
                        ]
                        summary_content = (
                            summary_before_think
                            + current_response[last_think_end + 8 :]
                        )
                    else:
                        thinking_content = current_response[last_think_start + 7 :]
                        summary_content = summary_before_think
                else:
                    summary_content = current_response

                yield thinking_content, summary_content

        except Exception as e:
            logger.error(f"Streaming summarization failed: {e}")
            raise SummarizationModelError(
                "要約のストリーミング生成に失敗しました。"
            ) from e
        finally:
            # Reset processing state
            self.is_summarizing = False

        # Final processing when streaming is complete
        final_response = "".join(stream_parts)
        if conv_s:
            thinking_content, summary_content = conv_s.extract_think_content(
                final_response
            )
        else:
            thinking_content, summary_content = "", final_response

        # Store final results in instance variables
        self.thinking = thinking_content
        self.summary = summary_content

        yield thinking_content, summary_content

    def reset(self):
        """Reset the summarization model state."""
        self.summary = ""
        self.thinking = ""
        self.is_summarizing = False

    def _build_prompt(self, text: str) -> str:
        """Constructs the prompt for the summarization task."""
        return f"""以下のテキストを日本語で要約してください。

テキスト:
{text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""
