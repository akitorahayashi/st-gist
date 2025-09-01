import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.services.conversation_service import ConversationService

@pytest.fixture
def mock_client():
    """Fixture for a mock client."""
    client = Mock()

    async def mock_generate(prompt):
        response = f"Response to {prompt}"
        for char in response:
            yield char
            await asyncio.sleep(0.01)

    client.generate = mock_generate
    return client

@pytest.fixture
def conversation_service(mock_client):
    """Fixture for ConversationService."""
    return ConversationService(client=mock_client)

class TestConversationService:
    """Test suite for ConversationService."""

    def test_initialization(self, mock_client):
        """Test that the service is initialized correctly."""
        service = ConversationService(mock_client)
        assert service.client == mock_client

    @pytest.mark.parametrize("messages, is_ai_thinking, expected", [
        ([], False, False),  # No messages
        ([{"role": "ai", "content": "Hello"}], False, False),  # Last message not from user
        ([{"role": "user", "content": "Hi"}], True, False),  # AI is already thinking
        ([{"role": "user", "content": "Hi"}], False, True),  # Valid case to start thinking
        ([{"role": "ai", "content": "Hello"}, {"role": "user", "content": "Question"}], False, True) # Valid case
    ])
    def test_should_start_ai_thinking(self, conversation_service, messages, is_ai_thinking, expected):
        """Test the logic for when the AI should start responding."""
        result = conversation_service.should_start_ai_thinking(messages, is_ai_thinking)
        assert result == expected

    @pytest.mark.asyncio
    async def test_generate_response_streaming(self, conversation_service):
        """Test that generate_response returns a proper async generator."""
        prompt = "test prompt"
        response_generator = conversation_service.generate_response(prompt)

        import inspect
        assert inspect.isasyncgen(response_generator)

        # Verify the streamed content
        chunks = [chunk async for chunk in response_generator]
        full_response = "".join(chunks)

        assert full_response == f"Response to {prompt}"

    @pytest.mark.asyncio
    async def test_generate_response_with_mock_client(self):
        """Test streaming response generation using a detailed mock."""
        mock_client = Mock()

        async def async_generator():
            yield "Hello"
            yield " "
            yield "World"

        # The mock should return an async generator when `generate` is called
        mock_client.generate = Mock(return_value=async_generator())

        service = ConversationService(client=mock_client)

        # Get the stream and collect results
        stream = service.generate_response("any prompt")
        results = [item async for item in stream]

        assert "".join(results) == "Hello World"
        mock_client.generate.assert_called_once_with("any prompt")
