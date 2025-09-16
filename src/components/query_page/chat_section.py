import asyncio
import html

import streamlit as st

from src.models import ConversationModel


def render_chat_section(
    conversation_model: ConversationModel, scraping_model, summarization_model
):
    """Render chat section with conversation functionality"""

    _render_chat_messages(
        conversation_model.messages, is_thinking=conversation_model.is_responding
    )

    prompt = st.chat_input(
        "このWebページへの質問", disabled=conversation_model.is_responding
    )

    if prompt:
        conversation_model.add_user_message(prompt)
        st.rerun()

    # If the last message is from the user and we should respond
    if conversation_model.should_respond():
        conversation_model.is_responding = True
        st.rerun()

    # Handle AI response generation
    if conversation_model.is_responding:
        try:
            user_query = conversation_model.messages[-1]["content"]
            # Get page content from scraping model
            page_content = scraping_model.content if scraping_model else ""
            # Get summary from summarization model
            page_summary = summarization_model.summary if summarization_model else ""

            # Create new event loop for chat response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                ai_message_object = loop.run_until_complete(
                    conversation_model.respond_to_user_message(
                        user_query,
                        summary=page_summary,
                        page_content=page_content,
                    )
                )
            finally:
                loop.close()

            # Display thinking process if available
            if ai_message_object.think and ai_message_object.think.strip():
                st.markdown("### 🤔 AI思考過程")
                with st.expander("思考プロセス", expanded=True):
                    st.markdown(ai_message_object.think)

            # Add only the content part to chat history (think is handled separately)
            conversation_model.add_ai_message(ai_message_object.content or "")
        except Exception as e:
            error_message = f"エラーが発生しました: {e}"
            conversation_model.last_error = error_message
            conversation_model.add_ai_message(error_message)
        finally:
            conversation_model.is_responding = False
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
