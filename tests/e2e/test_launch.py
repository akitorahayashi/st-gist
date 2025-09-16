import os
import subprocess
import time
from typing import Optional

import requests
import toml


def load_secrets(secrets_file: str = ".streamlit/secrets.toml") -> dict:
    """Load secrets from a TOML file."""
    try:
        with open(secrets_file, "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


class StreamlitE2ETest:
    """Generic E2E test class for any Streamlit application"""

    def __init__(
        self,
        app_path: str = "src/main.py",
        main_module: str = "src.main",
        test_port: Optional[str] = None,
        host_ip: Optional[str] = None,
        python_executable: Optional[str] = None,
    ):
        self.app_path = app_path
        self.main_module = main_module

        secrets = load_secrets()
        self.test_port = test_port or secrets.get("TEST_PORT", "8502")
        self.host_ip = host_ip or secrets.get("HOST_IP", "localhost")

        self.project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        if python_executable is None:
            self.python_executable = os.path.join(
                self.project_root, ".venv", "bin", "python"
            )
        else:
            self.python_executable = python_executable

        self.full_app_path = os.path.join(self.project_root, self.app_path)

    def test_package_import(self):
        """Test that the main module imports without missing dependencies."""
        result = subprocess.run(
            [self.python_executable, "-c", f"import {self.main_module}"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            assert False, f"Package import failed:\n{result.stderr}"

    def test_streamlit_app_starts_without_errors(self):
        """Test that Streamlit starts and serves content without errors."""
        process = subprocess.Popen(
            [
                self.python_executable,
                "-m",
                "streamlit",
                "run",
                self.full_app_path,
                f"--server.port={self.test_port}",
                "--server.headless=true",
            ],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            time.sleep(5)

            if process.poll() is not None:
                stdout, stderr = process.communicate()
                assert False, f"Streamlit crashed:\n{stderr}"

            response = requests.get(
                f"http://{self.host_ip}:{self.test_port}", timeout=3
            )

            if response.status_code != 200:
                assert False, f"Server returned status {response.status_code}"

            # Basic check - if we got here, server is working

        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


# Test functions using the StreamlitE2ETest helper
def test_package_import():
    """Test that the main module imports without missing dependencies."""
    test_helper = StreamlitE2ETest()
    return test_helper.test_package_import()


def test_streamlit_app_starts_without_errors():
    """Test that Streamlit starts and serves content without errors."""
    test_helper = StreamlitE2ETest()
    return test_helper.test_streamlit_app_starts_without_errors()
