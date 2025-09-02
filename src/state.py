from typing import Any, Dict, List, Optional

import streamlit as st


class AppState:
    """
    Manages the application's session state, providing a centralized and controlled
    interface for all state operations.
    """

    def __init__(self):
        # Initialize state keys with default values in st.session_state
        # This ensures that all keys are available from the start.
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "show_chat" not in st.session_state:
            st.session_state.show_chat = False
        if "processing" not in st.session_state:
            st.session_state.processing = False
        if "target_url" not in st.session_state:
            st.session_state.target_url = ""
        if "page_summary" not in st.session_state:
            st.session_state.page_summary = ""
        if "current_thinking" not in st.session_state:
            st.session_state.current_thinking = ""
        if "last_error" not in st.session_state:
            st.session_state.last_error = None
        if "scraped_content" not in st.session_state:
            st.session_state.scraped_content = ""
        if "ai_thinking" not in st.session_state:
            st.session_state.ai_thinking = False
        if "streaming" not in st.session_state:
            st.session_state.streaming = False
        if "stream_parts" not in st.session_state:
            st.session_state.stream_parts = []
        if "stream_iterator" not in st.session_state:
            st.session_state.stream_iterator = None

    # --- Properties for reading state ---

    @property
    def messages(self) -> List[Dict[str, str]]:
        return st.session_state.messages

    @property
    def show_chat(self) -> bool:
        return st.session_state.show_chat

    @property
    def is_processing(self) -> bool:
        return st.session_state.processing

    @property
    def target_url(self) -> str:
        return st.session_state.target_url

    @property
    def page_summary(self) -> str:
        return st.session_state.page_summary

    @property
    def current_thinking(self) -> str:
        return st.session_state.current_thinking

    @property
    def last_error(self) -> Optional[str]:
        return st.session_state.last_error

    @property
    def scraped_content(self) -> str:
        return st.session_state.scraped_content

    @property
    def is_ai_thinking(self) -> bool:
        return st.session_state.ai_thinking

    @property
    def is_streaming(self) -> bool:
        return st.session_state.streaming

    @property
    def stream_parts(self) -> List[str]:
        return st.session_state.stream_parts

    @property
    def stream_iterator(self) -> Optional[Any]:
        return st.session_state.stream_iterator

    # --- Methods for modifying state ---

    def initialize(self):
        """Initializes the session state."""
        self.reset_for_new_url()

    def start_summarization(self, url: str):
        """Starts the summarization process."""
        self.clear_error()
        st.session_state.processing = True
        st.session_state.target_url = url
        st.session_state.show_chat = False

    def complete_summarization(self, scraped_content: str):
        """Completes the summarization process."""
        st.session_state.processing = False
        st.session_state.scraped_content = scraped_content
        st.session_state.show_chat = True
        st.session_state.target_url = ""

    def set_summary_and_thinking(self, summary: str, thinking: str):
        """Sets the summary and thinking content."""
        st.session_state.page_summary = summary
        st.session_state.current_thinking = thinking

    def add_user_message(self, content: str):
        """Adds a user message to the chat history."""
        st.session_state.messages.append({"role": "user", "content": content})

    def start_ai_response(self):
        """Sets the state for starting an AI response."""
        st.session_state.ai_thinking = True

    def add_ai_message(self, content: str):
        """Adds a new AI message to the chat history."""
        st.session_state.messages.append({"role": "ai", "content": content})

    def complete_ai_response(self):
        """Sets the state for completing an AI response."""
        st.session_state.ai_thinking = False

    def reset_for_new_url(self):
        """Resets the state for a new URL submission."""
        st.session_state.messages = []
        st.session_state.page_summary = ""
        st.session_state.current_thinking = ""
        st.session_state.last_error = None
        st.session_state.target_url = ""
        st.session_state.scraped_content = ""
        st.session_state.show_chat = False
        st.session_state.processing = False
        st.session_state.ai_thinking = False
        st.session_state.streaming = False
        st.session_state.stream_parts = []
        st.session_state.stream_iterator = None

    def reset_chat(self):
        """Resets only the chat history."""
        st.session_state.messages = []
        st.session_state.ai_thinking = False

    def set_error(self, message: str):
        """Sets an error message and stops processing."""
        st.session_state.last_error = message
        st.session_state.processing = False
        st.session_state.ai_thinking = False

    def clear_error(self):
        """Clears any existing error message."""
        st.session_state.last_error = None

    def set_streaming(self, streaming: bool):
        st.session_state.streaming = streaming

    def set_stream_iterator(self, iterator: Optional[Any]):
        st.session_state.stream_iterator = iterator

    def append_stream_part(self, part: str):
        st.session_state.stream_parts.append(part)

    def clear_stream_parts(self):
        st.session_state.stream_parts = []

    def clear_scraped_content(self):
        st.session_state.scraped_content = ""

    
