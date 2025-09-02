from enum import Enum
from typing import Optional

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
        st.session_state.page = Page.INPUT

        # Reset all model states
        if "scraping_model" in st.session_state:
            st.session_state.scraping_model.reset()
        if "summarization_model" in st.session_state:
            st.session_state.summarization_model.reset()
        if "conversation_model" in st.session_state:
            st.session_state.conversation_model.reset()

    def go_to_chat_page(self):
        """Navigate to chat page."""
        st.session_state.page = Page.CHAT

    # --- URL state methods ---

    def set_target_url(self, url: str):
        """Save URL to session state for processing"""
        st.session_state.target_url = url


# Initialize app_router only if it doesn't exist
if "app_router" not in st.session_state:
    st.session_state.app_router = AppRouter()
