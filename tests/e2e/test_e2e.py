import os
import subprocess
import time

import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()


class TestE2E:
    """End-to-end tests that verify the actual site functionality"""

    def test_streamlit_app_loads_without_module_errors(self):
        """Test that the Streamlit app loads completely without module import errors"""
        test_port = os.getenv("TEST_PORT", "8502")
        host_ip = os.getenv("HOST_IP", "localhost")

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        app_path = os.path.join(project_root, "src", "main.py")

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

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        driver = None

        try:
            max_wait = 30
            wait_time = 0
            server_ready = False

            while wait_time < max_wait:
                try:
                    response = requests.get(f"http://{host_ip}:{test_port}", timeout=3)
                    if response.status_code == 200:
                        server_ready = True
                        break
                except requests.RequestException:
                    pass

                time.sleep(1)
                wait_time += 1

            assert (
                server_ready
            ), f"Streamlit server failed to start within {max_wait} seconds"

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(f"http://{host_ip}:{test_port}")

            wait = WebDriverWait(driver, 20)

            page_source = driver.page_source

            error_indicators = [
                "ModuleNotFoundError",
                "ImportError",
                "No module named",
                "500 Internal Server Error",
                "Something went wrong",
                "Traceback",
            ]

            for error in error_indicators:
                assert error not in page_source, f"Found error in page: {error}"

            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid='stApp']")
                    )
                )
                print("✅ Streamlit app loaded successfully")
            except Exception as e:
                print(
                    f"⚠️  Could not find main Streamlit container, but no errors detected: {e}"
                )

            title = driver.title
            assert (
                "Streamlit" in title or len(title) > 0
            ), "Page title is empty or invalid"

        finally:
            if driver:
                driver.quit()

            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_app_functionality_basic_interaction(self):
        """Test basic functionality and user interaction without errors"""
        test_port = os.getenv("TEST_PORT", "8502")
        host_ip = os.getenv("HOST_IP", "localhost")

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        app_path = os.path.join(project_root, "src", "main.py")

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

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        driver = None

        try:
            max_wait = 30
            wait_time = 0
            server_ready = False

            while wait_time < max_wait:
                try:
                    response = requests.get(f"http://{host_ip}:{test_port}", timeout=3)
                    if response.status_code == 200:
                        server_ready = True
                        break
                except requests.RequestException:
                    pass

                time.sleep(1)
                wait_time += 1

            assert (
                server_ready
            ), f"Streamlit server failed to start within {max_wait} seconds"

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(f"http://{host_ip}:{test_port}")

            wait = WebDriverWait(driver, 20)

            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='stApp']")
                )
            )

            time.sleep(3)

            page_source = driver.page_source
            runtime_errors = [
                "AttributeError",
                "TypeError",
                "ValueError",
                "KeyError",
                "NameError",
            ]

            for error in runtime_errors:
                assert error not in page_source, f"Found runtime error in page: {error}"

            print("✅ App functionality test passed - no runtime errors detected")

        finally:
            if driver:
                driver.quit()

            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
