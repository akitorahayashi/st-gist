import asyncio
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

    async def stream_summary(self, app_state: "AppState") -> None:
        """
        Handle stream generation from scraped content.
        
        Args:
            app_state: The application state instance to update during streaming.
        """
        # Import here to avoid circular imports
        from src.services.conversation_service import ConversationService
        
        conv_s = None
        # Get conversation service from session state (needed for extract_think_content)
        import streamlit as st
        if "conversation_service" in st.session_state:
            conv_s = st.session_state.get("conversation_service")
        
        has_summary = app_state.page_summary or app_state.current_thinking

        # Start streaming if we have scraped content but no summary
        if app_state.scraped_content and not has_summary and not app_state.is_streaming:
            app_state.set_streaming(True)
            app_state.clear_stream_parts()

            truncated_content = app_state.scraped_content[:10000]
            prompt = self._build_prompt(truncated_content)
            app_state.set_stream_iterator(self.llm_client.generate(prompt))

            return

        # Handle streaming process with improved real-time processing
        if app_state.is_streaming and app_state.stream_iterator:
            try:
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Process multiple chunks for smoother streaming
                chunks_processed = 0
                max_chunks_per_run = (
                    3  # Process multiple chunks per rerun for summarization
                )

                while chunks_processed < max_chunks_per_run:
                    try:
                        chunk = await app_state.stream_iterator.__anext__()
                        app_state.append_stream_part(chunk)
                        chunks_processed += 1

                        # Update display after each chunk
                        current_response = "".join(app_state.stream_parts)
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

                        app_state.set_summary_and_thinking(
                            summary_content, thinking_content
                        )

                    except StopAsyncIteration:
                        final_response = "".join(app_state.stream_parts)
                        if conv_s:
                            thinking_content, summary_content = conv_s.extract_think_content(
                                final_response
                            )
                        else:
                            thinking_content, summary_content = "", final_response
                        app_state.set_summary_and_thinking(
                            summary_content, thinking_content
                        )

                        app_state.set_streaming(False)
                        app_state.clear_scraped_content()
                        app_state.set_stream_iterator(None)
                        app_state.clear_stream_parts()
                        break

            except StopAsyncIteration:
                final_response = "".join(app_state.stream_parts)
                if conv_s:
                    thinking_content, summary_content = conv_s.extract_think_content(
                        final_response
                    )
                else:
                    thinking_content, summary_content = "", final_response
                app_state.set_summary_and_thinking(summary_content, thinking_content)

                app_state.set_streaming(False)
                app_state.clear_scraped_content()
                app_state.set_stream_iterator(None)
                app_state.clear_stream_parts()

    def _build_prompt(self, text: str) -> str:
        """Constructs the prompt for the summarization task."""
        return f"""以下のテキストを日本語で要約してください。

テキスト:
{text}

要約は以下の形式で出力してください。
タイトル: 記事の内容を一行で表すタイトルを1つ生成してください。
要点: 記事の最も重要なポイントを3つを目安として、最大5つまでの箇条書きで簡潔にまとめてください。各箇条書きは100字以内にしてください。
"""
