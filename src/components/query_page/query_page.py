import streamlit as st
from src.components.query_page.chat_ui import render_chat_messages, render_thinking_bubble, render_ai_message
from src.components.sidebar import render_sidebar


def render_query_page():
    """Render query page with URL summary and chat functionality"""
    st.title("ページ分析チャット")
    
    # Show URL being analyzed with back button
    if "target_url" in st.session_state:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**分析中のページ:** {st.session_state.target_url}")
        with col2:
            if st.button("新しいURLを入力", type="secondary"):
                st.session_state.show_chat = False
                if "messages" in st.session_state:
                    st.session_state.messages = []
                if "target_url" in st.session_state:
                    del st.session_state.target_url
                st.rerun()
        st.markdown("---")
    
    # Initialize messages if not exists or if it's a new session
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = []
        # Add initial summary message
        summary_content = st.session_state.get("page_summary", "このページの要約を作成しました。以下が主な内容です：\n\n• ページのメインテーマと概要\n• 重要なポイントや情報\n• 構造や特徴的な要素\n\nこのページについて何か質問はありますか？")
        summary_message = {
            "role": "assistant", 
            "content": summary_content
        }
        st.session_state.messages.append(summary_message)
    
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
    if st.session_state.get("ai_thinking", False):
        # Show thinking bubble only before streaming starts
        if not st.session_state.get("streaming_active", False):
            st.markdown(render_thinking_bubble(), unsafe_allow_html=True)

        st.session_state.conversation_service.handle_ai_thinking()


def check_start_ai_thinking():
    """Check if AI should start thinking"""
    if st.session_state.conversation_service.should_start_ai_thinking():
        st.session_state.ai_thinking = True
        st.rerun()