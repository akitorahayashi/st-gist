import pytest
import toml


@pytest.fixture
def secrets():
    with open(".streamlit/secrets.toml", "r") as f:
        return toml.load(f)
