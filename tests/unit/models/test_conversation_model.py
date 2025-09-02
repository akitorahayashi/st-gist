import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.models.conversation_model import ConversationModel


@pytest.fixture
def mock_client():
    """Fixture for a mocked client."""
    client = MagicMock()
    # Mock the async method
    client.generate_once = AsyncMock(return_value="AI response")
    return client


@pytest.fixture
def conversation_model(mock_client):
    """Fixture for a ConversationModel instance."""
    return ConversationModel(client=mock_client)


class TestConversationModel:
    def test_add_user_message(self, conversation_model):
        """Test that a user message is added correctly."""
        conversation_model.add_user_message("Hello")
        assert conversation_model.messages == [{"role": "user", "content": "Hello"}]

    def test_add_ai_message(self, conversation_model):
        """Test that an AI message is added correctly."""
        conversation_model.add_ai_message("Hi there")
        assert conversation_model.messages == [{"role": "ai", "content": "Hi there"}]

    def test_reset(self, conversation_model):
        """Test that the reset method clears messages."""
        conversation_model.add_user_message("A message")
        conversation_model.reset()
        assert conversation_model.messages == []

    # --- should_respond tests ---
    def test_should_respond_true(self, conversation_model):
        """Test should_respond returns True when the last message is from the user."""
        conversation_model.add_user_message("Question?")
        assert conversation_model.should_respond() is True

    def test_should_respond_false_if_last_is_ai(self, conversation_model):
        """Test should_respond returns False when the last message is from the AI."""
        conversation_model.add_user_message("Question?")
        conversation_model.add_ai_message("Answer.")
        assert conversation_model.should_respond() is False

    def test_should_respond_false_if_empty(self, conversation_model):
        """Test should_respond returns False when there are no messages."""
        assert conversation_model.should_respond() is False

    def test_should_respond_false_if_responding(self, conversation_model):
        """Test should_respond returns False when already responding."""
        conversation_model.add_user_message("Question?")
        conversation_model.is_responding = True
        assert conversation_model.should_respond() is False

    # --- extract_think_content tests ---
    @pytest.mark.parametrize(
        "text, expected_think, expected_clean",
        [
            (
                "<think>This is a thought.</think>This is the response.",
                "This is a thought.",
                "This is the response.",
            ),
            (
                "No think tags here.",
                "",
                "No think tags here.",
            ),
            (
                "<think>First thought.</think>Some text.<think>Second thought.</think>",
                "First thought.\nSecond thought.",
                "Some text.",
            ),
            (
                "Text without closing tag <think>should not break",
                "",
                "Text without closing tag <think>should not break",
            ),
        ],
    )
    def test_extract_think_content(
        self, conversation_model, text, expected_think, expected_clean
    ):
        """Test the extraction of content from <think> tags."""
        thinking_content, cleaned_text = conversation_model.extract_think_content(text)
        assert thinking_content == expected_think
        assert cleaned_text == expected_clean

    # --- respond_to_user_message test ---
    @pytest.mark.asyncio
    async def test_respond_to_user_message(self, conversation_model, mock_client):
        """Test the respond_to_user_message method."""
        response = await conversation_model.respond_to_user_message("User question")
        mock_client.generate_once.assert_called_once_with("User question")
        assert response == "AI response"
        assert not conversation_model.is_responding

    # --- limit_messages test ---
    def test_limit_messages(self, conversation_model):
        """Test that messages are correctly limited in session_state."""
        mock_session_state = MagicMock()
        mock_session_state.messages = [{"role": "user", "content": str(i)} for i in range(15)]

        with patch("streamlit.session_state", mock_session_state):
            conversation_model.limit_messages(max_messages=10)
            assert len(mock_session_state.messages) == 10
            assert mock_session_state.messages[0]["content"] == "5" # Check if the oldest messages were removed
