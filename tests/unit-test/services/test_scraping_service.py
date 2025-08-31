import pytest
from unittest.mock import patch, Mock
import requests
from src.services.scraping_service import ScrapingService


class TestScrapingService:
    
    def setup_method(self):
        self.scraping_service = ScrapingService()
    
    def test_validate_url_valid_http(self):
        """Test URL validation with valid HTTP URL."""
        # Should not raise exception
        self.scraping_service.validate_url("http://example.com")
    
    def test_validate_url_valid_https(self):
        """Test URL validation with valid HTTPS URL."""
        # Should not raise exception
        self.scraping_service.validate_url("https://example.com")
    
    def test_validate_url_invalid_scheme(self):
        """Test URL validation with invalid scheme."""
        with pytest.raises(ValueError, match="URLは http/https のみ対応しています"):
            self.scraping_service.validate_url("ftp://example.com")
    
    def test_validate_url_no_hostname(self):
        """Test URL validation with missing hostname."""
        with pytest.raises(ValueError, match="URLのホスト名が不正です"):
            self.scraping_service.validate_url("https://")
    
    @patch('src.services.scraping_service.socket.getaddrinfo')
    def test_validate_url_private_host(self, mock_getaddrinfo):
        """Test URL validation with private IP address."""
        # Mock getaddrinfo to return private IP
        mock_getaddrinfo.return_value = [
            (None, None, None, None, ('192.168.1.1', None))
        ]
        
        with pytest.raises(ValueError, match="指定のホストは許可されていません"):
            self.scraping_service.validate_url("https://private.com")
    
    @patch('src.services.scraping_service.requests.get')
    def test_scrape_success(self, mock_get):
        """Test successful scraping."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.content = b'<html><body><p>Test content</p></body></html>'
        mock_get.return_value = mock_response
        
        # Mock URL validation to avoid private IP check
        with patch.object(self.scraping_service, 'validate_url'):
            result = self.scraping_service.scrape("https://example.com")
        
        assert "Test content" in result
        mock_get.assert_called_once()
    
    @patch('src.services.scraping_service.requests.get')
    def test_scrape_request_exception(self, mock_get):
        """Test scraping with request exception."""
        mock_get.side_effect = requests.RequestException("Connection error")
        
        with patch.object(self.scraping_service, 'validate_url'):
            with pytest.raises(ValueError, match="コンテンツ取得に失敗しました"):
                self.scraping_service.scrape("https://example.com")
    
    @patch('src.services.scraping_service.requests.get')
    def test_scrape_non_html_content(self, mock_get):
        """Test scraping with non-HTML content."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response
        
        with patch.object(self.scraping_service, 'validate_url'):
            result = self.scraping_service.scrape("https://example.com")
        
        assert result == ""
    
    def test_is_private_host_localhost(self):
        """Test private host detection for localhost."""
        with patch('src.services.scraping_service.socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (None, None, None, None, ('127.0.0.1', None))
            ]
            assert self.scraping_service._is_private_host("localhost") is True
    
    def test_is_private_host_public(self):
        """Test private host detection for public IP."""
        with patch('src.services.scraping_service.socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (None, None, None, None, ('8.8.8.8', None))
            ]
            assert self.scraping_service._is_private_host("google.com") is False