import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "../../.venv/lib/python3.12/site-packages/sdk"
    ),
)

from olm_api_sdk.v2.mock_client import MockOlmClientV2

from src.models.conversation_model import ConversationModel
from src.models.scraping_model import ScrapingModel
from src.models.summarization_model import SummarizationModel


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
def mock_llm_client():
    """Fixture for MockOlmClientV2 with test responses."""
    return MockOlmClientV2(
        token_delay=0.001,  # Fast for tests
        responses=[
            "This is a summary of the content.",
            "This is the AI's response to your question.",
            "I understand. Let me help you with that.",
        ],
    )


@pytest.fixture
def scraping_model():
    """Fixture for ScrapingModel."""
    return ScrapingModel()


@pytest.fixture
def summarization_model(mock_llm_client):
    """Fixture for SummarizationModel with mock client."""
    return SummarizationModel(llm_client=mock_llm_client)


@pytest.fixture
def conversation_model(mock_llm_client):
    """Fixture for ConversationModel with mock client."""
    return ConversationModel(client=mock_llm_client)


@pytest.fixture
def mock_secrets():
    """Mock streamlit secrets for consistent test environment."""
    secrets_dict = {
        "SUMMARY_MODEL": "test-summary-model",
        "QUESTION_MODEL": "test-question-model",
        "MAX_PROMPT_LENGTH": 4000,
        "CONTEXT_MAX_LENGTH": 1500,
    }
    with patch("streamlit.secrets") as mock_st_secrets:
        mock_st_secrets.get.side_effect = lambda key, default=None: secrets_dict.get(
            key, default
        )
        yield mock_st_secrets
