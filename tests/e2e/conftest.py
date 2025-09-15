import os
import subprocess

import pytest
import toml


@pytest.fixture(scope="session")
def available_models():
    """Returns a list of available local ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")
        models = [line.split()[0] for line in lines[1:]]
        return models
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []


@pytest.fixture(scope="session")
def secrets(available_models):
    """
    Loads secrets from .streamlit/secrets.toml, with a fallback to secrets.example.toml,
    and provides a fallback for TEST_MODEL.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    secrets_path = os.path.join(project_root, ".streamlit", "secrets.toml")
    example_secrets_path = os.path.join(
        project_root, ".streamlit", "secrets.example.toml"
    )

    secrets_data = {}
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            secrets_data = toml.load(f)
    elif os.path.exists(example_secrets_path):
        with open(example_secrets_path, "r") as f:
            secrets_data = toml.load(f)

    test_model = secrets_data.get("TEST_MODEL")

    # Set a fallback model if TEST_MODEL is not defined or not available
    if not test_model or test_model not in available_models:
        if available_models:
            if "qwen3:1.7b" in available_models:
                test_model = "qwen3:1.7b"
            else:
                test_model = available_models[0]
        else:
            test_model = None  # No models available

    secrets_data["TEST_MODEL"] = test_model

    if "OLM_API_ENDPOINT" in secrets_data and "OLLAMA_HOST" not in secrets_data:
        secrets_data["OLLAMA_HOST"] = secrets_data["OLM_API_ENDPOINT"]

    return secrets_data
