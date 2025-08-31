import os

import streamlit as st

from clients.ollama_api_client import OllamaApiClient
from components.chat_ui import render_chat_messages, render_thinking_bubble
from components.sidebar import render_sidebar
from services.conversation_service import ConversationService


def main():
    st.title("Bubble Chat UI")
    initialize_session()
    draw_sidebar()
    handle_user_input()
    draw_chat_messages()
    handle_ai_response()
    check_start_ai_thinking()


def initialize_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "ollama_client" not in st.session_state:
        is_debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        if is_debug:
            import sys

            sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
            from dev.mocks.mock_ollama_client import MockOllamaApiClient

            st.session_state.ollama_client = MockOllamaApiClient()
            st.sidebar.success("🚧 DEBUG MODE: Using Mock Client")
        else:
            st.session_state.ollama_client = OllamaApiClient()
            st.sidebar.info("🌐 Using Real Ollama API")
    if "conversation_service" not in st.session_state:
        st.session_state.conversation_service = ConversationService(
            st.session_state.ollama_client
        )


def draw_sidebar():
    render_sidebar()


def draw_chat_messages():
    render_chat_messages(st.session_state.messages)


def handle_user_input():
    is_ai_thinking = st.session_state.get("ai_thinking", False)

    if is_ai_thinking:
        st.chat_input("AIが応答中です...", disabled=True)
        return

    user_input = st.chat_input("メッセージを入力")
    if user_input is not None:
        user_input = user_input.strip()
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.rerun()


def handle_ai_response():
    if st.session_state.get("ai_thinking", False):
        # Show thinking bubble only before streaming starts
        if not st.session_state.get("streaming_active", False):
            st.markdown(render_thinking_bubble(), unsafe_allow_html=True)

        st.session_state.conversation_service.handle_ai_thinking()


def check_start_ai_thinking():
    if st.session_state.conversation_service.should_start_ai_thinking():
        st.session_state.ai_thinking = True
        st.rerun()


if __name__ == "__main__":
    main()
