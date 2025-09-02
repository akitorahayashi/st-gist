import os

import streamlit as st
from dotenv import load_dotenv

from src.clients.ollama_client import OllamaApiClient
from src.components.query_page import render_query_page
from src.components.url_input_page import render_url_input_page
from src.models import ConversationModel, ScrapingModel, SummarizationModel
from src.router import AppRouter, Page

# Load environment variables
load_dotenv()


def main():
    initialize_session()

    st.set_page_config(
        page_title="Gist",
        page_icon="📝",
        layout="centered"
    )

    # Route based on page state using AppRouter and Page Enum
    if st.session_state.app_router.current_page == Page.CHAT:
        render_query_page()
    else:  # default to Page.INPUT
        render_url_input_page()


def initialize_session():
    # Initialize AppRouter
    if "app_router" not in st.session_state:
        st.session_state.app_router = AppRouter()

    # Client should be initialized regardless of the page
    if "ollama_client" not in st.session_state:
        is_debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        if is_debug:
            from dev.mocks.clients.mock_ollama_client import MockOllamaApiClient

            st.session_state.ollama_client = MockOllamaApiClient()
        else:
            st.session_state.ollama_client = OllamaApiClient()

    # Initialize conversation model
    if "conversation_model" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.conversation_model = ConversationModel(
                st.session_state.ollama_client
            )

    # Initialize scraping model
    if "scraping_model" not in st.session_state:
        st.session_state.scraping_model = ScrapingModel()

    # Initialize summarization model
    if "summarization_model" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.summarization_model = SummarizationModel(
                st.session_state.ollama_client
            )


if __name__ == "__main__":
    main()
