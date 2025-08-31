import pytest
from unittest.mock import patch, Mock, AsyncMock
import httpx
import json
from src.clients.ollama_client import OllamaApiClient


class TestOllamaApiClient:
    
    def setup_method(self):
        with patch.dict('os.environ', {
            'OLLAMA_API_ENDPOINT': 'http://localhost:11434',
            'OLLAMA_MODEL': 'llama2'
        }):
            self.client = OllamaApiClient()
    
    def test_init_with_env_vars(self):
        """Test client initialization with environment variables."""
        with patch.dict('os.environ', {
            'OLLAMA_API_ENDPOINT': 'http://test:11434',
            'OLLAMA_MODEL': 'test-model'
        }):
            client = OllamaApiClient()
            assert client.api_url == 'http://test:11434'
            assert client.generate_endpoint == 'http://test:11434/api/v1/generate'
    
    
    
    
    def test_generate_without_model(self):
        """Test generate method without model parameter."""
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'default-model'}):
            with patch.object(self.client, '_stream_response') as mock_stream:
                mock_stream.return_value = AsyncMock()
                
                result = self.client.generate("test prompt")
                
                mock_stream.assert_called_once_with("test prompt", "default-model")
    
    def test_generate_with_model(self):
        """Test generate method with model parameter."""
        with patch.object(self.client, '_stream_response') as mock_stream:
            mock_stream.return_value = AsyncMock()
            
            result = self.client.generate("test prompt", "custom-model")
            
            mock_stream.assert_called_once_with("test prompt", "custom-model")
    
    def test_generate_without_model_env(self):
        """Test generate method without model parameter or environment variable."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OLLAMA_MODEL is not configured"):
                self.client.generate("test prompt")