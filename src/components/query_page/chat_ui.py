import html
from pathlib import Path

import streamlit as st
import toml


def load_chat_colors():
    """Load chat colors from config.toml"""
    config_path = Path(".streamlit/config.toml")
    if config_path.exists():
        config = toml.load(config_path)
        chat_config = config.get("chat", {})
        return {
            "user_color": chat_config.get("userMessageColor", "#007bff"),
            "ai_color": chat_config.get("aiMessageColor", "#f1f1f1"),
        }
    return {"user_color": "#007bff", "ai_color": "#f1f1f1"}


def get_chat_styles(user_color, ai_color):
    """Returns the consolidated CSS for the chat UI."""
    return f"""
    <style>
    .chat-container {{
        max-width: 800px;
        margin: 0 auto;
        padding: 0 16px;
    }}
    .user-message {{
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        margin: 10px 0;
    }}
    .user-content {{
        background-color: {user_color};
        color: white;
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 20px;
        word-wrap: break-word;
    }}
    .ai-message {{
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
        margin: 10px 0;
    }}
    .ai-content {{
        background-color: {ai_color};
        color: #333;
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 20px;
        word-wrap: break-word;
    }}
    .thinking-message {{
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
        margin: 10px 0;
    }}
    .thinking-content {{
        background-color: {ai_color};
        color: #333;
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 20px;
    }}
    .thinking-dots {{
        animation: thinking 1.5s infinite;
    }}
    @keyframes thinking {{
        0%, 50%, 100% {{ opacity: 1; }}
        25%, 75% {{ opacity: 0.5; }}
    }}
    </style>
    """


def render_user_message(message):
    """Render user message without inline styles"""
    return f"""
    <div class="user-message">
        <div class="user-content">
            {html.escape(message).replace(chr(10), '<br>')}
        </div>
    </div>
    """


def render_ai_message(message):
    """Render AI message without inline styles"""
    return f"""
    <div class="ai-message">
        <div class="ai-content">
            {html.escape(message).replace(chr(10), '<br>')}
        </div>
    </div>
    """


def render_thinking_bubble():
    """Render AI thinking bubble without inline styles"""
    return '''
    <div class="thinking-message">
        <div class="thinking-content">
            <div style="display: flex; align-items: center;">
                <div class="thinking-dots">
                    Thinking...
                </div>
            </div>
        </div>
    </div>
    '''


def render_chat_messages(messages, is_thinking=False):
    """
    Render all chat messages with a single style block by building a single HTML string.
    Also renders the thinking bubble if is_thinking is True.
    """
    messages_html_list = []
    for msg in messages:
        if msg["role"] == "user":
            messages_html_list.append(render_user_message(msg["content"]))
        else:
            messages_html_list.append(render_ai_message(msg["content"]))
            
    # is_thinkingがTrueの場合、思考中バブルをリストの末尾に追加
    if is_thinking:
        messages_html_list.append(render_thinking_bubble())

    messages_html_string = "".join(messages_html_list)

    colors = load_chat_colors()
    styles = get_chat_styles(colors["user_color"], colors["ai_color"])

    full_html = f"""
    {styles}
    <div class="chat-container">
    {messages_html_string}
    </div>
    """

    st.markdown(full_html, unsafe_allow_html=True)