import pytest
import requests
from unittest.mock import MagicMock, patch

from src.models.scraping_model import ScrapingModel


@pytest.fixture
def scraping_model():
    """Returns a ScrapingModel instance."""
    return ScrapingModel()


class TestScrapingModel:
    # --- validate_url tests ---
    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com",
        ],
    )
    def test_validate_url_valid(self, scraping_model, url):
        """Test that validate_url accepts valid URLs."""
        # This should not raise any exception
        scraping_model.validate_url(url)

    @pytest.mark.parametrize(
        "url, error_message",
        [
            ("ftp://example.com", "URLは http/https のみ対応しています。"),
            ("http://127.0.0.1", "指定のホストは許可されていません。"),
            ("https://192.168.1.1", "指定のホストは許可されていません。"),
            ("http://localhost", "指定のホストは許可されていません。"),
            ("http://invalid.hostname.local", "指定されたホスト 'invalid.hostname.local' が見つかりません。URLを確認してください。"),
        ],
    )
    def test_validate_url_invalid(self, scraping_model, url, error_message):
        """Test that validate_url rejects invalid URLs."""
        with pytest.raises(ValueError, match=error_message):
            scraping_model.validate_url(url)

    # --- scrape tests ---
    @patch("requests.get")
    def test_scrape_success(self, mock_get, scraping_model):
        """Test successful scraping and content cleaning."""
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <header>Header</header>
                <nav>Navigation</nav>
                <main>
                    <h1>Main Content</h1>
                    <p>This is a paragraph.</p>
                </main>
                <script>alert('hello');</script>
                <style>body { color: red; }</style>
                <footer>Footer</footer>
                <aside>Aside</aside>
            </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode("utf-8")
        mock_response.headers = {"Content-Type": "text/html"}
        mock_get.return_value = mock_response

        content = scraping_model.scrape("http://example.com")
        assert content == "Main Content This is a paragraph."
        assert scraping_model.content == "Main Content This is a paragraph."
        assert not scraping_model.is_scraping

    @patch("requests.get")
    def test_scrape_http_error(self, mock_get, scraping_model):
        """Test that scrape handles HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.RequestException("HTTP Error")
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="コンテンツ取得に失敗しました: HTTP Error"):
            scraping_model.scrape("http://example.com")
        assert not scraping_model.is_scraping

    def test_scrape_invalid_url(self, scraping_model):
        """Test that scrape raises ValueError for invalid URL."""
        with pytest.raises(ValueError, match="指定のホストは許可されていません。"):
            scraping_model.scrape("http://127.0.0.1")
        assert not scraping_model.is_scraping
