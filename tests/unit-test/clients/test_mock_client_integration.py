import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from dev.mocks.mock_ollama_client import MockOllamaApiClient
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


class TestMockClientIntegration:
    """Test suite for integration between ConversationService and MockOllamaApiClient"""

    @pytest.fixture
    def mock_st(self):
        """Mock streamlit module"""
        with patch("src.services.conversation_service.st") as mock_st:
            mock_st.session_state = MockStreamlitSessionState()
            mock_st.rerun = lambda: None
            mock_st.error = lambda msg: print(f"ERROR: {msg}")
            yield mock_st

    @pytest.fixture
    def mock_client(self):
        """Create real MockOllamaApiClient instance"""
        return MockOllamaApiClient()

    @pytest.fixture
    def conversation_service(self, mock_client, mock_st):
        """Create ConversationService with real mock client"""
        return ConversationService(mock_client)

    @pytest.mark.asyncio
    async def test_mock_client_streaming(self, mock_client):
        """Test that MockOllamaApiClient streaming works without errors"""
        # This test would have failed before fixing CHARACTER_DELAY
        response_chunks = []
        async for chunk in mock_client.generate("test"):
            response_chunks.append(chunk)

        # Should get some response
        assert len(response_chunks) > 0
        full_response = "".join(response_chunks)
        assert "test response" in full_response.lower()

    def test_conversation_service_with_mock_client_streaming(
        self, conversation_service, mock_st
    ):
        """Test ConversationService using actual MockOllamaApiClient streaming"""
        # Set up initial state
        mock_st.session_state.messages = [{"role": "user", "content": "hello"}]
        mock_st.session_state.ai_thinking = True
        mock_st.session_state.streaming_active = False

        # This should not raise an error about CHARACTER_DELAY
        try:
            conversation_service.handle_ai_thinking()
            # If we get here, the streaming initialization worked
            assert True
        except NameError as e:
            if "CHARACTER_DELAY" in str(e):
                pytest.fail("CHARACTER_DELAY error still exists in mock client")
            else:
                raise

    def test_prepare_streaming_chunks_integration(self, conversation_service, mock_st):
        """Test _prepare_streaming_chunks with real mock client"""
        mock_st.session_state.messages = [{"role": "user", "content": "test"}]
        mock_st.session_state.streaming_response = (
            ""  # Initialize this to prevent += error
        )

        # This should work without CHARACTER_DELAY error
        try:
            conversation_service._prepare_streaming_chunks("test message")
            # Check that chunks were prepared
            assert "stream_chunks" in mock_st.session_state
            assert "chunk_index" in mock_st.session_state
        except NameError as e:
            if "CHARACTER_DELAY" in str(e):
                pytest.fail("CHARACTER_DELAY error in streaming preparation")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
