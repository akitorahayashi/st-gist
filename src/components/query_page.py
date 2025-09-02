import asyncio
import html

import streamlit as st

from src.components.sidebar import render_sidebar
from src.services.conversation_service import ConversationService
from src.services.summarization_service import SummarizationService
from src.app_state import AppState


def render_query_page():
    """Render query page with URL summary and chat functionality"""
    app_state: AppState = st.session_state.app_state
    conv_s: ConversationService = st.session_state.get("conversation_service")
    
    # Initialize summarization service
    ollama_client = st.session_state.get("ollama_client")
    summarization_service = None
    if ollama_client:
        summarization_service = SummarizationService(ollama_client)

    # Load CSS for query page styling
    try:
        with open("src/static/css/query_page.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, continue without styling

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
    if summarization_service and (app_state.scraped_content and not (app_state.page_summary or app_state.current_thinking) and not app_state.is_streaming):
        asyncio.run(summarization_service.stream_summary(app_state))
        st.rerun()
    elif app_state.is_streaming and summarization_service:
        asyncio.run(summarization_service.stream_summary(app_state))
        st.rerun()

    # Add divider before chat if we have content
    if app_state.current_thinking.strip() or app_state.page_summary.strip():
        st.markdown("---")

    # Render sidebar
    render_sidebar()

    # --- Chat Logic --- #
    _render_chat_messages(app_state.messages, is_thinking=app_state.is_ai_thinking)

    prompt = st.chat_input("このWebページへの質問", disabled=app_state.is_ai_thinking)

    if prompt:
        app_state.add_user_message(prompt)
        app_state.start_ai_response()  # Set thinking to True
        st.rerun()

    # If the last message is from the user and we are in the thinking state
    if (
        app_state.is_ai_thinking
        and app_state.messages
        and app_state.messages[-1]["role"] == "user"
    ):
        try:
            response = asyncio.run(
                conv_s.generate_response_once(app_state.messages[-1]["content"])
            )
            _, clean_response = conv_s.extract_think_content(response)
            app_state.add_ai_message(clean_response)
        except Exception as e:
            error_message = f"エラーが発生しました: {e}"
            app_state.set_error(error_message)  # This will also complete_ai_response
            _, clean_error = conv_s.extract_think_content(error_message)
            app_state.add_ai_message(clean_error)
        finally:
            # This might be redundant if set_error is called, but it's safe
            if app_state.is_ai_thinking:
                app_state.complete_ai_response()
            st.rerun()


def _render_chat_messages(messages, is_thinking=False):
    """
    Render all chat messages with a single style block by building a single HTML string.
    Also renders the thinking bubble if is_thinking is True.
    """
    messages_html_list = []
    for msg in messages:
        if msg["role"] == "user":
            messages_html_list.append(
                f"""
    <div class="user-message">
        <div class="user-content">
            {html.escape(msg["content"]).replace(chr(10), '<br>')}
        </div>
    </div>
    """
            )
        else:
            messages_html_list.append(
                f"""
    <div class="ai-message">
        <div class="ai-content">
            {html.escape(msg["content"]).replace(chr(10), '<br>')}
        </div>
    </div>
    """
            )

    # is_thinkingがTrueの場合、思考中バブルをリストの末尾に追加
    if is_thinking:
        messages_html_list.append(
            """
    <div class="thinking-message">
        <div class="thinking-content">
            <div style="display: flex; align-items: center;">
                <div class="thinking-dots">
                    Thinking...
                </div>
            </div>
        </div>
    </div>
    """
        )

    messages_html_string = "".join(messages_html_list)

    full_html = f"""
    <div class="chat-container">
    {messages_html_string}
    </div>
    """

    st.markdown(full_html, unsafe_allow_html=True)


