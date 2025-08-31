import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from src.services.conversation_service import ConversationService


class MockStreamlitSessionState:
    """Mock Streamlit session state for testing"""

    def __init__(self):
        self._state = {}

    def get(self, key, default=None):
        return self._state.get(key, default)

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self._state[key] = value

    def __contains__(self, key):
        return key in self._state

    def __getattr__(self, name):
        return self._state.get(name)

    def __setattr__(self, name, value):
        if name == "_state":
            super().__setattr__(name, value)
        else:
            self._state[name] = value

    def __delitem__(self, key):
        if key in self._state:
            del self._state[key]


class TestConversationService:
    """Test suite for ConversationService"""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing"""
        client = Mock()

        async def mock_generate(prompt, model=None):
            # Mock streaming response
            test_response = "Test response"
            for char in test_response:
                yield char

        client.generate = mock_generate
        return client

    @pytest.fixture
    def mock_st(self):
        """Mock streamlit module"""
        with patch("src.services.conversation_service.st") as mock_st:
            mock_st.session_state = MockStreamlitSessionState()
            mock_st.rerun = Mock()
            yield mock_st

    @pytest.fixture
    def conversation_service(self, mock_client, mock_st):
        """Create ConversationService instance for testing"""
        return ConversationService(mock_client)

    def test_init(self, mock_client):
        """Test ConversationService initialization"""
        service = ConversationService(mock_client)
        assert service.client == mock_client

    def test_should_start_ai_thinking_empty_messages(
        self, conversation_service, mock_st
    ):
        """Test should_start_ai_thinking with empty messages"""
        mock_st.session_state.messages = []
        result = conversation_service.should_start_ai_thinking()
        assert result is False

    def test_should_start_ai_thinking_no_user_message(
        self, conversation_service, mock_st
    ):
        """Test should_start_ai_thinking with no user message"""
        mock_st.session_state.messages = [{"role": "ai", "content": "Hello"}]
        result = conversation_service.should_start_ai_thinking()
        assert result is False

    def test_should_start_ai_thinking_already_thinking(
        self, conversation_service, mock_st
    ):
        """Test should_start_ai_thinking when already thinking"""
        mock_st.session_state.messages = [{"role": "user", "content": "Hello"}]
        mock_st.session_state["ai_thinking"] = True
        result = conversation_service.should_start_ai_thinking()
        assert result is False

    def test_should_start_ai_thinking_valid(self, conversation_service, mock_st):
        """Test should_start_ai_thinking with valid conditions"""
        mock_st.session_state.messages = [{"role": "user", "content": "Hello"}]
        mock_st.session_state["ai_thinking"] = False
        result = conversation_service.should_start_ai_thinking()
        assert result is True

    def test_limit_messages_under_limit(self, conversation_service, mock_st):
        """Test limit_messages when under limit"""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(5)]
        mock_st.session_state.messages = messages
        conversation_service.limit_messages(max_messages=10)
        assert len(mock_st.session_state.messages) == 5

    def test_limit_messages_over_limit(self, conversation_service, mock_st):
        """Test limit_messages when over limit"""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(15)]
        mock_st.session_state.messages = messages
        conversation_service.limit_messages(max_messages=10)
        assert len(mock_st.session_state.messages) == 10
        # Check that it kept the last 10 messages
        assert mock_st.session_state.messages[0]["content"] == "Message 5"
        assert mock_st.session_state.messages[-1]["content"] == "Message 14"

    def test_handle_ai_thinking_not_thinking(self, conversation_service, mock_st):
        """Test handle_ai_thinking when not in thinking state"""
        mock_st.session_state["ai_thinking"] = False
        conversation_service.handle_ai_thinking()
        # Should not modify state
        assert not mock_st.session_state.get("streaming_started", False)

    def test_handle_ai_thinking_streaming_start(self, conversation_service, mock_st):
        """Test handle_ai_thinking starts streaming"""
        mock_st.session_state.messages = [{"role": "user", "content": "Test message"}]
        mock_st.session_state["ai_thinking"] = True
        mock_st.session_state["streaming_active"] = False

        with patch.object(conversation_service, "_start_streaming") as mock_start:
            conversation_service.handle_ai_thinking()
            mock_start.assert_called_once()

    def test_handle_ai_thinking_streaming_continue(self, conversation_service, mock_st):
        """Test handle_ai_thinking continues streaming"""
        mock_st.session_state["ai_thinking"] = True
        mock_st.session_state["streaming_active"] = True

        with patch.object(conversation_service, "_continue_streaming") as mock_continue:
            conversation_service.handle_ai_thinking()
            mock_continue.assert_called_once()

    def test_start_streaming(self, conversation_service, mock_st):
        """Test _start_streaming initializes correctly"""
        mock_st.session_state.messages = [{"role": "user", "content": "Test message"}]

        with patch.object(
            conversation_service, "_prepare_streaming_chunks"
        ) as mock_prepare:
            conversation_service._start_streaming()

            assert mock_st.session_state.get("streaming_active") is True
            assert mock_st.session_state.get("streaming_response") == ""
            assert mock_st.session_state.get("streaming_complete") is False
            assert len(mock_st.session_state.messages) == 2
            assert mock_st.session_state.messages[-1]["role"] == "ai"
            mock_prepare.assert_called_once_with("Test message")

    def test_cleanup_streaming(self, conversation_service, mock_st):
        """Test _cleanup_streaming clears state"""
        # Set up streaming state
        mock_st.session_state["ai_thinking"] = True
        mock_st.session_state["streaming_active"] = True
        mock_st.session_state["stream_chunks"] = ["T", "e", "s", "t"]

        conversation_service._cleanup_streaming()

        assert mock_st.session_state.get("ai_thinking") is False
        assert mock_st.session_state.get("streaming_active") is False
        assert mock_st.session_state.get("stream_chunks") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
