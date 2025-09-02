from enum import Enum
from typing import Optional

import streamlit as st


class Page(Enum):
    """Enumeration for application pages"""

    INPUT = "input"
    CHAT = "chat"


class AppRouter:
    """
    Manages application routing and global UI state.
    Provides centralized navigation and state management functionality.
    """

    def __init__(self):
        """Initialize router and ensure required session state keys exist."""
        # Initialize page routing
        if "page" not in st.session_state:
            st.session_state.page = Page.INPUT

        # Initialize UI state keys
        if "processing" not in st.session_state:
            st.session_state.processing = False
        if "last_error" not in st.session_state:
            st.session_state.last_error = None

    # --- Properties for reading state ---

    @property
    def current_page(self) -> Page:
        """Get the current page."""
        return st.session_state.page

    @property
    def is_processing(self) -> bool:
        """Check if the application is currently processing."""
        return st.session_state.processing

    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message, if any."""
        return st.session_state.last_error

    # --- Navigation methods ---

    def go_to_input_page(self):
        """Navigate to input page and reset UI state."""
        st.session_state.page = Page.INPUT
        st.session_state.processing = False
        st.session_state.last_error = None

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
        st.session_state.processing = False

    # --- Processing state methods ---

    def start_processing(self):
        """Start processing state."""
        self.clear_error()
        st.session_state.processing = True

    def stop_processing(self):
        """Stop processing state."""
        st.session_state.processing = False

    # --- Error handling methods ---

    def set_error(self, message: str):
        """Set error message and stop processing."""
        st.session_state.last_error = message
        st.session_state.processing = False

    def clear_error(self):
        """Clear any existing error message."""
        st.session_state.last_error = None


# Initialize app_router in session_state if it doesn't exist
if "app_router" not in st.session_state:
    st.session_state.app_router = AppRouter()
