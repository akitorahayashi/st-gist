import os

import streamlit as st
from dotenv import load_dotenv
from sdk.olm_api_client import MockOllamaApiClient, OllamaApiClient

from src.components.query_page import render_query_page
from src.components.url_input_page import render_url_input_page
from src.models import ConversationModel, ScrapingModel, SummarizationModel
from src.router import AppRouter, Page
from src.services.vector_store import VectorStore

# Load environment variables
load_dotenv()


@st.cache_resource
def load_summarization_model(_client):
    """SummarizationModelをキャッシュしてロードする"""
    return SummarizationModel(_client)


@st.cache_resource
def load_conversation_model(_client):
    """ConversationModelをキャッシュしてロードする"""
    return ConversationModel(_client)


@st.cache_resource
def load_vector_store():
    """VectorStoreをキャッシュしてロードする"""
    return VectorStore()


def main():
    st.set_page_config(page_title="Gist", page_icon="📝", layout="centered")

    initialize_session()

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
            st.session_state.ollama_client = MockOllamaApiClient(token_delay=0.01)
        else:
            ollama_api_endpoint = os.getenv("OLM_API_ENDPOINT")
            if not ollama_api_endpoint:
                # Fallback to Streamlit secrets if available
                try:
                    ollama_api_endpoint = st.secrets.get("OLM_API_ENDPOINT")
                except Exception:
                    pass

            if not ollama_api_endpoint:
                raise ValueError(
                    "OLM_API_ENDPOINT is not configured in environment variables or Streamlit secrets."
                )

            st.session_state.ollama_client = OllamaApiClient(
                api_url=ollama_api_endpoint
            )

    # Initialize summarization model
    if "summarization_model" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.summarization_model = load_summarization_model(
                st.session_state.ollama_client
            )

    # Initialize conversation model
    if "conversation_model" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.conversation_model = load_conversation_model(
                st.session_state.ollama_client
            )

    # Initialize scraping model
    if "scraping_model" not in st.session_state:
        st.session_state.scraping_model = ScrapingModel()

    # Initialize vector store
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = load_vector_store()


if __name__ == "__main__":
    main()
