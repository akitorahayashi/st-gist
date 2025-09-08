import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st  # noqa: E402
from sdk.olm_api_client import MockOllamaApiClient, OllamaApiClient  # noqa: E402

from src.components.query_page.query_page import render_query_page  # noqa: E402
from src.components.sidebar.sidebar import render_sidebar  # noqa: E402
from src.components.url_input.url_input_page import render_url_input_page  # noqa: E402
from src.models import (  # noqa: E402
    ConversationModel,
    ScrapingModel,
    SummarizationModel,
    VectorStore,
)
from src.router import AppRouter, Page  # noqa: E402


@st.cache_data
def load_model(model_class, _client):
    """モデルをセッション毎にキャッシュしてロードする"""
    return model_class(_client)


st.set_page_config(
    page_title="Gist",
    page_icon="💎",
    # "centered"/"wide"
    layout="centered",
    # "auto"/"expanded"/"collapsed"
    initial_sidebar_state="auto",
)


def main():

    initialize_session()

    # Route based on page state using AppRouter and Page Enum
    if st.session_state.app_router.current_page == Page.CHAT:
        render_query_page()
        render_sidebar(Page.CHAT)
    else:  # default to Page.INPUT
        render_url_input_page()
        render_sidebar(Page.INPUT)


def initialize_session():
    # Initialize AppRouter
    if "app_router" not in st.session_state:
        st.session_state.app_router = AppRouter()

    # セッション初期化を確実にするため、アプリケーション開始時の状態確認
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
        # 既存のキャッシュされたデータをクリア
        st.cache_data.clear()

    # Client should be initialized regardless of the page
    if "ollama_client" not in st.session_state:
        is_debug = st.secrets.get("DEBUG", False)
        if is_debug:
            st.session_state.ollama_client = MockOllamaApiClient(token_delay=0.01)
        else:
            ollama_api_endpoint = st.secrets.get("OLM_API_ENDPOINT")
            if not ollama_api_endpoint:
                raise ValueError(
                    "OLM_API_ENDPOINT is not configured in Streamlit secrets."
                )

            st.session_state.ollama_client = OllamaApiClient(
                api_url=ollama_api_endpoint
            )

    # Initialize summarization model
    if "summarization_model" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.summarization_model = load_model(
                SummarizationModel, st.session_state.ollama_client
            )

    # Initialize conversation model
    if "conversation_model" not in st.session_state:
        if "ollama_client" in st.session_state:
            st.session_state.conversation_model = load_model(
                ConversationModel, st.session_state.ollama_client
            )

    # Initialize scraping model
    if "scraping_model" not in st.session_state:
        st.session_state.scraping_model = ScrapingModel()

    # Initialize vector store and load the embedding model
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = VectorStore()


if __name__ == "__main__":
    main()
