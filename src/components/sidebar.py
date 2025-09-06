import streamlit as st

from src.router import Page


def render_sidebar(page: Page = None):
    """Render sidebar with page-specific controls"""
    app_router = st.session_state.app_router
    current_page = page or app_router.current_page

    with st.sidebar:

        if current_page == Page.CHAT:
            # Chat page sidebar options
            if st.button(
                "🏠 New URL",
                help="新しいサイトを分析",
                key="new_url_btn",
                use_container_width=True,
            ):
                app_router.go_to_input_page()
                st.rerun()

            if st.button(
                "✨ New Chat",
                help="チャットをクリア",
                key="new_chat_btn",
                use_container_width=True,
            ):
                st.session_state.conversation_model.reset()
                st.rerun()

        elif current_page == Page.INPUT:
            # URL input page sidebar options
            st.markdown("### 📚 おすすめのまとめサイト")

            st.link_button(
                "💼 TechCrunch",
                url="https://techcrunch.com/",
                help="技術・スタートアップニュース",
                use_container_width=True,
            )
            
            st.link_button(
                "📰 AI News",
                url="https://artificialintelligence-news.com/",
                help="最新のAIニュース",
                use_container_width=True,
            )
            
            st.link_button(
                "✨ Synced Review",
                url="https://syncedreview.com/",
                help="AI技術レビュー",
                use_container_width=True,
            )
