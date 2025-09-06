from string import Template
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.models.conversation_model import ConversationModel


@pytest.fixture
def mock_client():
    """Fixture for a mocked client."""
    client = MagicMock()
    # Mock the async method
    client.gen_batch = AsyncMock(return_value="AI response")
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

    def test_format_chat_history(self, conversation_model):
        """Test the _format_chat_history method."""
        conversation_model.add_user_message("Hello")
        conversation_model.add_ai_message("Hi there")
        conversation_model.add_user_message("How are you?")
        # The last message is not included in the history
        history = conversation_model._format_chat_history()
        expected_history = "ユーザー: Hello\nAI: Hi there"
        assert history == expected_history

    def test_format_chat_history_empty(self, conversation_model):
        """Test the _format_chat_history method with no history."""
        history = conversation_model._format_chat_history()
        assert history == ""

    # --- respond_to_user_message test ---
    @pytest.mark.asyncio
    @patch("src.models.conversation_model.st.secrets")
    async def test_respond_to_user_message(
        self, mock_secrets, conversation_model, mock_client
    ):
        """Test the respond_to_user_message method."""

        def get_secret(key, default=None):
            if key == "QUESTION_MODEL":
                return "test-model"
            if key == "MAX_PROMPT_LENGTH":
                return 4000
            return default

        mock_secrets.get.side_effect = get_secret

        user_question = "User question"
        # Build the expected prompt using the model's template
        template_content = conversation_model._qa_prompt_template.template
        expected_prompt = Template(template_content).safe_substitute(
            summary="",
            user_message=user_question,
            chat_history="",
            vector_search_content="",
            page_content="",
        )

        response = await conversation_model.respond_to_user_message(user_question)

        # Verify that the gen_batch method was called with the correct prompt and model
        mock_client.gen_batch.assert_called_once_with(
            expected_prompt, model="test-model"
        )
        assert response == "AI response"
        assert not conversation_model.is_responding

    # --- _load_qa_prompt_template tests ---
    def test_load_qa_prompt_template_success(self, conversation_model):
        """Test that the QA prompt template is loaded correctly."""
        mock_template_content = "Template: $user_message"
        # The actual path being opened by the model implementation
        target_path = "src/static/prompts/web_page_qa_prompt.md"

        with patch(
            "builtins.open", mock_open(read_data=mock_template_content)
        ) as mock_file:
            # We patch the path within the model's __init__ to avoid complex path logic
            with patch(
                "src.models.conversation_model.os.path.join", return_value=target_path
            ):
                template = conversation_model._load_qa_prompt_template()

                mock_file.assert_called_once_with(target_path, "r", encoding="utf-8")
                assert isinstance(template, Template)
                assert template.template == mock_template_content

    def test_load_qa_prompt_template_file_not_found(self, conversation_model):
        """Test that FileNotFoundError is raised when the template file is not found."""
        target_path = "src/static/prompts/web_page_qa_prompt.md"

        with patch("builtins.open", side_effect=FileNotFoundError) as mock_file:
            with patch(
                "src.models.conversation_model.os.path.join", return_value=target_path
            ):
                with pytest.raises(FileNotFoundError):
                    conversation_model._load_qa_prompt_template()
                mock_file.assert_called_once_with(target_path, "r", encoding="utf-8")

    # --- limit_messages test ---
    def test_limit_messages(self, conversation_model):
        """Test that messages are correctly limited in the model's state."""
        # Add 15 messages directly to the model
        conversation_model.messages = [
            {"role": "user", "content": str(i)} for i in range(15)
        ]

        # Limit the messages to 10
        conversation_model.limit_messages(max_messages=10)

        # Assert that the length is now 10
        assert len(conversation_model.messages) == 10

        # Assert that the oldest messages were removed
        # The first message should now be the one with content "5"
        assert conversation_model.messages[0]["content"] == "5"
