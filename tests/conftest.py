import os
import sys

import pytest
import toml

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def secrets():
    with open(".streamlit/secrets.toml", "r") as f:
        return toml.load(f)
