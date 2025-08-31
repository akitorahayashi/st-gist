import os
import subprocess
import time

import requests
from dotenv import load_dotenv

load_dotenv()


class TestBuild:

    def test_streamlit_server_startup(self):
        """Test that Streamlit server can start and respond to requests"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        app_path = os.path.join(project_root, "src", "main.py")
        
        host_ip = os.getenv("HOST_IP", "localhost")
        test_port = os.getenv("TEST_PORT", "8502")

        # Start Streamlit server in background
        process = subprocess.Popen(
            [
                "poetry",
                "run",
                "streamlit",
                "run",
                app_path,
                f"--server.port={test_port}",
                "--server.headless=true",
            ],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Wait for server to start (max 15 seconds)
            max_wait = 15
            wait_time = 0
            server_ready = False

            while wait_time < max_wait:
                try:
                    response = requests.get(f"http://{host_ip}:{test_port}", timeout=2)
                    if response.status_code == 200:
                        server_ready = True
                        break
                except requests.RequestException:
                    pass

                time.sleep(1)
                wait_time += 1

            # If server didn't start, capture error output for debugging
            if not server_ready:
                stdout, stderr = process.communicate(timeout=5)
                error_msg = f"Streamlit server failed to start within {max_wait} seconds"
                if stderr:
                    error_msg += f"\nStderr: {stderr}"
                if stdout:
                    error_msg += f"\nStdout: {stdout}"
                assert False, error_msg

            # Test that the server is actually serving the app
            response = requests.get(f"http://{host_ip}:{test_port}", timeout=5)
            assert (
                response.status_code == 200
            ), f"Server responded with status {response.status_code}"

        finally:
            # Clean up: terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
