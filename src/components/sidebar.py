import streamlit as st


def render_sidebar():
    """Render sidebar with chat controls"""
    app_router = st.session_state.app_router

    with st.sidebar:

        if st.button(
            "🏠 New URL",
            help="新しいURLを分析するため、URLを入力するページに戻ります。現在のチャット履歴と要約内容はクリアされます。",
            key="new_url_btn",
            use_container_width=True,
        ):
            app_router.go_to_input_page()
            st.rerun()

        if st.button(
            "✨ New Chat",
            help="チャット履歴のみクリアして新しい会話を開始します。要約内容は保持されます。",
            key="new_chat_btn",
            use_container_width=True,
        ):
            st.session_state.conversation_model.reset()
            st.rerun()
