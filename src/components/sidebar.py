import streamlit as st


def render_sidebar():
    """Render sidebar with chat controls"""
    app_router = st.session_state.app_router

    with st.sidebar:

        if st.button(
            "🏠 New URL",
            help="新しいURLを入力するページに戻る",
            key="new_url_btn",
            use_container_width=True,
        ):
            app_router.go_to_input_page()
            st.rerun()

        if st.button(
            "✨ New Chat",
            help="Clear history and start a new chat",
            key="new_chat_btn",
            use_container_width=True,
        ):
            st.session_state.conversation_model.reset()
            st.rerun()
