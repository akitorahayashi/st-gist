import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import toml
from streamlit.testing.v1 import AppTest

# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add SDK path for UI tests
sdk_path = os.path.join(
    project_root, ".venv", "lib", "python3.12", "site-packages", "sdk"
)
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)


@pytest.fixture
def mock_secrets():
    """Mock streamlit secrets for consistent UI testing."""
    secrets_dict = {
        "DEBUG": True,
        "USE_LOCAL_OLLAMA": False,
        "OLM_API_ENDPOINT": "http://mock-api:8000",
        "SUMMARY_MODEL": "test-summary-model",
        "QUESTION_MODEL": "test-question-model",
        "MAX_PROMPT_LENGTH": 4000,
        "CONTEXT_MAX_LENGTH": 1500,
    }

    # Create a temporary secrets file for AppTest
    temp_secrets = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    toml.dump(secrets_dict, temp_secrets)
    temp_secrets.close()

    # Mock st.secrets to return our test values
    with patch("streamlit.secrets") as mock_st_secrets:
        mock_st_secrets.get.side_effect = lambda key, default=None: secrets_dict.get(
            key, default
        )
        mock_st_secrets.toml_path = temp_secrets.name
        yield mock_st_secrets

    # Clean up temporary file
    os.unlink(temp_secrets.name)


@pytest.fixture
def app_secrets_file():
    """Create temporary secrets file for AppTest initialization."""
    secrets_dict = {
        "DEBUG": True,
        "USE_LOCAL_OLLAMA": False,
        "OLM_API_ENDPOINT": "http://mock-api:8000",
        "SUMMARY_MODEL": "test-summary-model",
        "QUESTION_MODEL": "test-question-model",
        "MAX_PROMPT_LENGTH": 4000,
        "CONTEXT_MAX_LENGTH": 1500,
    }

    # Create temporary .streamlit directory and secrets file
    temp_dir = tempfile.mkdtemp()
    streamlit_dir = os.path.join(temp_dir, ".streamlit")
    os.makedirs(streamlit_dir, exist_ok=True)

    secrets_file = os.path.join(streamlit_dir, "secrets.toml")
    with open(secrets_file, "w") as f:
        toml.dump(secrets_dict, f)

    # Change to temp directory for test
    old_cwd = os.getcwd()
    os.chdir(temp_dir)

    yield secrets_file

    # Cleanup
    os.chdir(old_cwd)
    import shutil

    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_models():
    """Create mock models for testing."""
    mock_scraping_model = MagicMock()
    mock_summarization_model = MagicMock()
    mock_conversation_model = MagicMock()

    # Default model states
    mock_summarization_model.summary = ""
    mock_summarization_model.thinking = ""
    mock_summarization_model.is_summarizing = False
    mock_summarization_model.last_error = None
    mock_summarization_model.reset = MagicMock()

    mock_conversation_model.messages = []
    mock_conversation_model.is_responding = False
    mock_conversation_model.should_respond = MagicMock(return_value=True)
    mock_conversation_model.reset = MagicMock()

    mock_scraping_model.validate_url = MagicMock(return_value=(True, ""))
    mock_scraping_model.scrape = MagicMock(return_value="Sample scraped content")

    return {
        "scraping": mock_scraping_model,
        "summarization": mock_summarization_model,
        "conversation": mock_conversation_model,
    }


@pytest.fixture
def app_test_with_mocks(app_secrets_file, mock_models):
    """Initialize AppTest with mocked models."""
    with patch("src.main.load_model") as mock_load_model:
        mock_load_model.side_effect = [
            mock_models["summarization"],
            mock_models["conversation"],
            mock_models["scraping"],
        ]

        # Use absolute path to main.py
        main_py_path = os.path.join(project_root, "src", "main.py")
        at = AppTest.from_file(main_py_path).run()
        yield at, mock_models
