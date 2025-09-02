import asyncio

import streamlit as st

from src.components.query_page.chat_ui import (
    render_chat_messages,
    render_thinking_bubble,
)
from src.components.sidebar import render_sidebar
from src.components.think_display import extract_think_content
from src.services.summarization_service import SummarizationService


def render_query_page():
    """Render query page with URL summary and chat functionality"""
    app_state = st.session_state.app_state
    st.title("Query Page")

    # Display thinking content if available
    if app_state.current_thinking.strip():
        st.markdown("### 🤔 AI の思考過程")
        with st.expander("思考プロセス", expanded=True):
            st.markdown(app_state.current_thinking)

    # Display summary content
    if app_state.page_summary.strip():
        st.markdown("### 📝 要約コンテンツ")
        st.markdown(app_state.page_summary)

    # Handle stream generation from scraped content
    handle_stream_generation()

    # Add divider before chat if we have content
    if app_state.current_thinking.strip() or app_state.page_summary.strip():
        st.markdown("---")

    # Render sidebar
    render_sidebar()

    # Render chat messages
    render_chat_messages(app_state.messages)

    # Show thinking bubble if AI is thinking but hasn't started streaming yet
    if app_state.is_ai_thinking and not app_state.stream_iterator:
        st.markdown(render_thinking_bubble(), unsafe_allow_html=True)

    # Handle user input
    handle_user_input()

    # Handle AI response
    handle_ai_response()

    # Check if AI should start thinking
    check_start_ai_thinking()


def handle_user_input():
    """Handle user input in chat"""
    app_state = st.session_state.app_state
    if app_state.is_ai_thinking:
        st.chat_input("AIが応答中です...", disabled=True)
        return

    user_input = st.chat_input("このページについて質問してください")
    if user_input is not None and user_input.strip():
        app_state.add_user_message(user_input.strip())
        st.rerun()


def handle_ai_response():
    """Handle AI response processing by managing the stream with improved real-time processing."""
    app_state = st.session_state.app_state

    if app_state.is_ai_thinking and app_state.stream_iterator:
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Process multiple chunks for better real-time experience
            chunks_processed = 0
            max_chunks_per_run = 5  # Process multiple chunks per rerun
            
            while chunks_processed < max_chunks_per_run:
                try:
                    chunk = loop.run_until_complete(app_state.stream_iterator.__anext__())
                    app_state.update_ai_response(chunk)
                    chunks_processed += 1
                except StopAsyncIteration:
                    app_state.complete_ai_response()
                    app_state.set_stream_iterator(None)
                    break
            
            st.rerun()
        except StopAsyncIteration:
            app_state.complete_ai_response()
            app_state.set_stream_iterator(None)
            st.rerun()


def check_start_ai_thinking():
    """Check if AI should start thinking and initiate the stream."""
    app_state = st.session_state.app_state
    svc = st.session_state.get("conversation_service")

    if svc and svc.should_start_ai_thinking(
        app_state.messages, app_state.is_ai_thinking
    ):
        app_state.start_ai_response()
        user_message = app_state.messages[-2][
            "content"
        ]  # User message is the second to last
        stream_iterator = svc.generate_response(user_message)
        app_state.set_stream_iterator(stream_iterator)
        st.rerun()


def handle_stream_generation():
    """Handle stream generation from scraped content"""
    app_state = st.session_state.app_state
    has_summary = app_state.page_summary or app_state.current_thinking

    # Start streaming if we have scraped content but no summary
    if app_state.scraped_content and not has_summary and not app_state.is_streaming:
        app_state.set_streaming(True)
        app_state.clear_stream_parts()

        ollama_client = st.session_state.get("ollama_client")
        if ollama_client:
            summarization_service = SummarizationService(ollama_client)
            truncated_content = app_state.scraped_content[:10000]
            prompt = summarization_service._build_prompt(truncated_content)
            app_state.set_stream_iterator(ollama_client.generate(prompt))

        st.rerun()
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
            max_chunks_per_run = 3  # Process multiple chunks per rerun for summarization
            
            while chunks_processed < max_chunks_per_run:
                try:
                    chunk = loop.run_until_complete(app_state.stream_iterator.__anext__())
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

                    app_state.set_summary_and_thinking(summary_content, thinking_content)
                    
                except StopAsyncIteration:
                    final_response = "".join(app_state.stream_parts)
                    thinking_content, summary_content = extract_think_content(final_response)
                    app_state.set_summary_and_thinking(summary_content, thinking_content)

                    app_state.set_streaming(False)
                    app_state.clear_scraped_content()
                    app_state.set_stream_iterator(None)
                    app_state.clear_stream_parts()
                    break
            
            st.rerun()
        except StopAsyncIteration:
            final_response = "".join(app_state.stream_parts)
            thinking_content, summary_content = extract_think_content(final_response)
            app_state.set_summary_and_thinking(summary_content, thinking_content)

            app_state.set_streaming(False)
            app_state.clear_scraped_content()
            app_state.set_stream_iterator(None)
            app_state.clear_stream_parts()
            st.rerun()
