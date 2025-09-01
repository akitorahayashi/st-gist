import os

import streamlit as st

from src.components.header import render_header
from src.clients.ollama_client import OllamaApiClient
from src.components.query_page import render_query_page
from src.components.url_input_page import render_url_input_page
from src.services.conversation_service import ConversationService


def main():
    initialize_session()


    # Complete component switching - only one renders at a time
    if st.session_state.get("show_chat", False):
        st.set_page_config(layout="wide")
        render_query_page()
    else:
        st.set_page_config(layout="centered")
        render_url_input_page()

    if not st.session_state.get("show_chat", False):
        render_header()

def initialize_session():
    # Client should be initialized regardless of the page
    if "ollama_client" not in st.session_state:
        is_debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        if is_debug:
            import sys

            sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
            from dev.mocks.mock_ollama_client import MockOllamaApiClient

            st.session_state.ollama_client = MockOllamaApiClient()
        else:
            st.session_state.ollama_client = OllamaApiClient()

    # Initialize messages for chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize conversation service only when needed (on chat page)
    if st.session_state.get("show_chat", False):
        if (
            "conversation_service" not in st.session_state
            and "ollama_client" in st.session_state
        ):
            st.session_state.conversation_service = ConversationService(
                st.session_state.ollama_client
            )


if __name__ == "__main__":
    main()
