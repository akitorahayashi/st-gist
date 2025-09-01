import asyncio

import streamlit as st

from src.components.query_page.chat_ui import (
    render_chat_messages,
    render_thinking_bubble,
)
from src.components.sidebar import render_sidebar
from src.components.think_display import extract_think_content, is_inside_think_tags
from src.services.summarization_service import SummarizationService


def render_query_page():
    """Render query page with URL summary and chat functionality"""
    st.title("Query Page")

    # Display thinking content if available
    thinking_content = st.session_state.get("current_thinking", "")
    if thinking_content.strip():
        st.markdown("### 🤔 AI の思考過程")
        with st.expander("思考プロセス", expanded=True):
            st.markdown(thinking_content)

    # Display summary content
    summary_content = st.session_state.get("page_summary", "")
    if summary_content.strip():
        st.markdown("### 📝 要約コンテンツ")
        st.markdown(summary_content)

    # Handle stream generation from scraped content - at the very end
    handle_stream_generation()

    # Add divider before chat if we have content
    if thinking_content.strip() or summary_content.strip():
        st.markdown("---")
    
    # Initialize messages if not exists or if it's a new session
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = []

    # Render sidebar
    render_sidebar()

    # Render chat messages
    render_chat_messages(st.session_state.messages)

    # Handle user input
    handle_user_input()

    # Handle AI response
    handle_ai_response()

    # Check if AI should start thinking
    check_start_ai_thinking()


def handle_user_input():
    """Handle user input in chat"""
    is_ai_thinking = st.session_state.get("ai_thinking", False)

    if is_ai_thinking:
        st.chat_input("AIが応答中です...", disabled=True)
        return

    user_input = st.chat_input("このページについて質問してください")
    if user_input is not None:
        user_input = user_input.strip()
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.rerun()


def handle_ai_response():
    """Handle AI response processing"""
    svc = st.session_state.get("conversation_service")
    if st.session_state.get("ai_thinking", False) and svc:
        if not st.session_state.get("streaming_active", False):
            st.markdown(render_thinking_bubble(), unsafe_allow_html=True)
        svc.handle_ai_thinking()


def check_start_ai_thinking():
    """Check if AI should start thinking"""
    svc = st.session_state.get("conversation_service")
    if svc and svc.should_start_ai_thinking():
        st.session_state.ai_thinking = True
        st.rerun()


def handle_stream_generation():
    """Handle stream generation from scraped content"""
    scraped_content = st.session_state.get("scraped_content")
    has_summary = st.session_state.get("page_summary") or st.session_state.get("current_thinking")
    is_streaming = st.session_state.get("streaming", False)
    
    # Start streaming if we have scraped content but no summary
    if scraped_content and not has_summary and not is_streaming:
        st.session_state.streaming = True
        st.session_state.stream_parts = []
        
        # Get ollama client and create prompt
        ollama_client = st.session_state.get("ollama_client")
        if ollama_client:
            summarization_service = SummarizationService(ollama_client)
            truncated_content = scraped_content[:10000]
            prompt = summarization_service._build_prompt(truncated_content)
            
            # Initialize stream iterator
            st.session_state.stream_iterator = ollama_client.generate(prompt)
        
        # Immediately rerun to clear previous UI and show streaming UI
        st.rerun()
        return  # Exit early to prevent further processing
    
    # Handle streaming process
    if is_streaming and "stream_iterator" in st.session_state:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                chunk = loop.run_until_complete(
                    st.session_state.stream_iterator.__anext__()
                )
                st.session_state.stream_parts.append(chunk)
                
                # Extract current content and separate think tags
                current_response = "".join(st.session_state.stream_parts)
                thinking_content, summary_content = extract_think_content(current_response)
                
                # Update session state with separated content
                if thinking_content.strip():
                    st.session_state.current_thinking = thinking_content
                
                # Only update summary if not inside think tags
                if summary_content.strip() and not is_inside_think_tags(current_response):
                    st.session_state.page_summary = summary_content
                
                # Continue streaming
                st.rerun()
                
            finally:
                loop.close()
                
        except StopAsyncIteration:
            # Stream completed
            final_response = "".join(st.session_state.stream_parts)
            thinking_content, summary_content = extract_think_content(final_response)
            
            # Store final content
            if thinking_content.strip():
                st.session_state.current_thinking = thinking_content
            if summary_content.strip():
                st.session_state.page_summary = summary_content
            
            # Clean up
            st.session_state.streaming = False
            st.session_state.pop("scraped_content", None)
            st.session_state.pop("stream_iterator", None)
            st.session_state.pop("stream_parts", None)
            
            st.rerun()


