import streamlit as st
import pyperclip

from src.router import Page


def render_sidebar(page: Page = None):
    """Render sidebar with page-specific controls"""
    app_router = st.session_state.app_router
    current_page = page or app_router.current_page

    with st.sidebar:

        if current_page == Page.CHAT:

            st.markdown("### Navigation")

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

            # 🔥 おすすめの記事セクションを追加
            st.markdown("### 🔥 おすすめの記事")
            if st.button(
                "自己学習AI SEAL",
                help="自己学習AI、SEAL",
                use_container_width=True,
                key="rec_seal_btn",
            ):
                pyperclip.copy("https://syncedreview.com/2025/06/16/mit-researchers-unveil-seal-a-new-step-towards-self-improving-ai/")
                st.session_state.copied_article = "自己学習AI、SEAL"
                st.rerun()

            if st.button(
                "トークン推論の先",
                help="トークン推論の先",
                use_container_width=True,
                key="token_infer_btn1",
            ):
                pyperclip.copy("https://example.com/article2")
                st.session_state.copied_article = "トークン推論の先"
                st.rerun()

            if st.button(
                "LLM自動故障帰因の研究",
                help="LLM自動故障帰因の研究",
                use_container_width=True,
                key="token_infer_btn2",
            ):
                pyperclip.copy("https://syncedreview.com/2025/08/14/which-agent-causes-task-failures-and-whenresearchers-from-psu-and-duke-explores-automated-failure-attribution-of-llm-multi-agent-systems/")
                st.session_state.copied_article = "LLM自動故障帰因の研究"
                st.rerun()

            # initialize copied_article state
            if "copied_article" not in st.session_state:
                st.session_state.copied_article = None

            # show info if an article was just copied
            if st.session_state.copied_article:
                st.info(f"{st.session_state.copied_article}の記事のリンクをコピーしました")

            st.markdown("### 📚 まとめサイト")
            
            st.link_button(
                "✨ Synced Review",
                url="https://syncedreview.com/",
                help="AI技術レビュー",
                use_container_width=True,
            )

            st.link_button(
                "💼 TechCrunch",
                url="https://techcrunch.com/",
                help="技術・スタートアップニュース",
                use_container_width=True,
            )
