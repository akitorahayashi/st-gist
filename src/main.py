import os

import streamlit as st

from src.clients.ollama_client import OllamaApiClient
from src.components.query_page import render_query_page
from src.components.url_input_page import render_url_input_page
from src.services.conversation_service import ConversationService
from src.state import AppState


def main():
    initialize_session()
    app_state = st.session_state.app_state

    # Complete component switching - only one renders at a time
    if app_state.show_chat:
        st.set_page_config(layout="centered")
        render_query_page()
    else:
        st.set_page_config(layout="centered")
        render_url_input_page()


def initialize_session():
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()

    # Client should be initialized regardless of the page
    if "ollama_client" not in st.session_state:
        is_debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        if is_debug:
            from dev.mocks.mock_ollama_client import MockOllamaApiClient

            st.session_state.ollama_client = MockOllamaApiClient()
        else:
            st.session_state.ollama_client = OllamaApiClient()

    # Initialize conversation service only when needed (on chat page)
    if "conversation_service" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.conversation_service = ConversationService(
                st.session_state.ollama_client
            )


if __name__ == "__main__":
    main()
