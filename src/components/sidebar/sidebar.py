import streamlit as st

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

            st.write(
                "任意のウェブサイトのURLをコピーして、テキストボックスに貼り付けてください。"
            )

            # 🔥 おすすめの記事
            st.markdown("### 🔥 おすすめの記事")
            st.link_button(
                "自己学習AI SEAL",
                url="https://syncedreview.com/2025/06/16/mit-researchers-unveil-seal-a-new-step-towards-self-improving-ai/",
                help="自己学習AI、SEAL",
                use_container_width=True,
            )
            st.link_button(
                "トークン推論の先",
                url="https://syncedreview.com/2024/12/17/self-evolving-prompts-redefining-ai-alignment-with-deepmind-chicago-us-eva-framework-15/",
                help="トークン推論の先",
                use_container_width=True,
            )
            st.link_button(
                "LLM自動故障帰因の研究",
                url="https://syncedreview.com/2025/08/14/which-agent-causes-task-failures-and-whenresearchers-from-psu-and-duke-explores-automated-failure-attribution-of-llm-multi-agent-systems/",
                help="LLM自動故障帰因の研究",
                use_container_width=True,
            )

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
