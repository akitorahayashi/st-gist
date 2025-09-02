import os
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src import main
from src.routing import Page


class MockStreamlitSessionState(dict):
    """A mock for st.session_state that acts like a dictionary."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)


@pytest.fixture
def mock_st_session():
    """Patches streamlit.session_state with a mock."""
    with patch("streamlit.session_state", MockStreamlitSessionState()) as mock_session:
        yield mock_session


@pytest.fixture
def initialized_models(mock_st_session):
    """
    Initializes the session with models, using a mock for the LLM client.
    This fixture ensures that `main.initialize_session()` is called
    within the patched context.
    """
    # Set DEBUG to true to use the MockOllamaApiClient
    with patch.dict(os.environ, {"DEBUG": "true"}):
        main.initialize_session()
    return mock_st_session


@pytest.mark.asyncio
async def test_full_app_flow(initialized_models):
    """
    Tests the full application flow from URL submission to chat interaction.
    """
    session = initialized_models

    # 1. Initial state check
    assert "scraping_model" in session
    assert "summarization_model" in session
    assert "conversation_model" in session
    assert session.app_router.current_page == Page.INPUT

    # --- Mock external dependencies ---
    # Mock ScrapingModel's scrape method
    scraping_model = session.scraping_model
    scraping_model.scrape = MagicMock(return_value="This is the scraped content.")

    # Mock SummarizationModel's stream_summary method
    summarization_model = session.summarization_model
    async def mock_stream_summary(content):
        summarization_model.thinking = "Thinking about the content."
        summarization_model.summary = "This is the summary."
        yield ("Thinking about the content.", "This is the summary.")
    summarization_model.stream_summary = mock_stream_summary

    # Mock ConversationModel's respond_to_user_message method
    conversation_model = session.conversation_model
    conversation_model.respond_to_user_message = AsyncMock(return_value="This is the AI's answer.")


    # 2. Scrape a URL
    test_url = "http://example.com"
    scraped_content = scraping_model.scrape(test_url)
    session.app_router.go_to_chat_page()  # Simulate page transition after scraping

    assert scraped_content == "This is the scraped content."
    assert session.app_router.current_page == Page.CHAT

    # 3. Generate summary
    # In the actual app, this is done via a service, we simulate it here
    async for _ in summarization_model.stream_summary(scraped_content):
        pass # Consume the generator

    assert summarization_model.thinking == "Thinking about the content."
    assert summarization_model.summary == "This is the summary."

    # 4. Interact with the chat
    user_message = "What is this about?"
    conversation_model.add_user_message(user_message)
    assert conversation_model.messages[-1] == {"role": "user", "content": user_message}

    # Check if we should respond
    assert conversation_model.should_respond() is True

    # Generate AI response
    ai_response = await conversation_model.respond_to_user_message(user_message)
    conversation_model.add_ai_message(ai_response)

    assert ai_response == "This is the AI's answer."
    assert conversation_model.messages[-1] == {"role": "ai", "content": "This is the AI's answer."}
    assert conversation_model.should_respond() is False # Last message is from AI, so should be false
