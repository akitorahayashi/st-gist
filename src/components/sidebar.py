import streamlit as st


def render_sidebar():
    """Render sidebar with chat controls"""
    with st.sidebar:

        if st.button(
            "🏠 New URL",
            help="新しいURLを入力するページに戻る",
            key="new_url_btn",
            use_container_width=True,
        ):
            st.session_state.show_chat = False
            if "messages" in st.session_state:
                st.session_state.messages = []
            if "target_url" in st.session_state:
                del st.session_state.target_url
            if "page_summary" in st.session_state:
                del st.session_state.page_summary
            if "ai_thinking" in st.session_state:
                del st.session_state.ai_thinking
            if "streaming_active" in st.session_state:
                del st.session_state.streaming_active
            st.rerun()

        if st.button(
            "✨ New Chat",
            help="Clear history and start a new chat",
            key="new_chat_btn",
            use_container_width=True,
        ):
            st.session_state["messages"] = []
            for k in ("ai_thinking", "streaming_active"):
                st.session_state.pop(k, None)
            st.rerun()
