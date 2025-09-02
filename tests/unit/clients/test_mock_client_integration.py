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
        # New mock should include specific test response and think tags
        # The response may have spacing due to tokenization, so check for key words
        assert "test" in full_response.lower()
        assert "mock client" in full_response.lower()
        assert (
            "everything" in full_response.lower()
            or "every thing" in full_response.lower()
        ) and (
            "working" in full_response.lower() or "wor king" in full_response.lower()
        )
        # Check for think tags (with possible spacing due to tokenization)
        assert "<think>" in full_response and "</think>" in full_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
