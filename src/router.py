from enum import Enum

import streamlit as st


class Page(Enum):
    """Enumeration for application pages"""

    INPUT = "input"
    CHAT = "chat"


class AppRouter:
    """
    Manages application routing.
    Provides centralized navigation functionality.
    """

    def __init__(self):
        """Initialize router and ensure required session state keys exist."""
        # Initialize page routing
        if "page" not in st.session_state:
            st.session_state.page = Page.INPUT

    # --- Properties for reading state ---

    @property
    def current_page(self) -> Page:
        """Get the current page."""
        return st.session_state.page

    # --- Navigation methods ---

    def go_to_input_page(self):
        """Navigate to input page and reset model states."""
        # Reset all model states before clearing session
        self._reset_all_model_states()

        # Preserving essential keys like 'app_router' and 'page'
        preserved_keys = {"app_router", "page"}
        for key in list(st.session_state.keys()):
            if key not in preserved_keys:
                del st.session_state[key]

        st.session_state.page = Page.INPUT

    def go_to_chat_page(self):
        """Navigate to chat page."""
        st.session_state.page = Page.CHAT

    # --- URL state methods ---

    def set_target_url(self, url: str):
        """Save URL to session state for processing"""
        st.session_state.target_url = url

    # --- Private helper methods ---

    def _reset_all_model_states(self):
        """Reset all model states to ensure clean session start"""
        # Reset conversation model if exists
        if "conversation_model" in st.session_state:
            st.session_state.conversation_model.reset()

        # Reset vector store if exists
        if "vector_store" in st.session_state:
            st.session_state.vector_store.reset()

        # Reset summarization model if exists
        if "summarization_model" in st.session_state:
            st.session_state.summarization_model.reset()

        # Reset scraping model if exists
        if "scraping_model" in st.session_state:
            st.session_state.scraping_model.reset()


# Initialize app_router only if it doesn't exist
if "app_router" not in st.session_state:
    st.session_state.app_router = AppRouter()
