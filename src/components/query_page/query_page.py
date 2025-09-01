import streamlit as st

from src.components.query_page.chat_ui import (
    render_chat_messages,
    render_thinking_bubble,
)
from src.components.sidebar import render_sidebar


def render_query_page():
    """Render query page with URL summary and chat functionality"""
    st.title("Query Page")

    # Display thinking content if available
    thinking_content = st.session_state.get("current_thinking", "")
    if thinking_content.strip():
        st.markdown("### 🤔 AI の思考過程")
        with st.expander("思考プロセス", expanded=False):
            st.markdown(thinking_content)

    # Display summary content
    summary_content = st.session_state.get("page_summary", "")
    if summary_content.strip():
        st.markdown("### 📝 要約コンテンツ")
        st.markdown(summary_content)
    
    # Show URL being analyzed
    if "target_url" in st.session_state:
        st.markdown(f"**URL:** {st.session_state.target_url}")

        # Add divider before chat
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
