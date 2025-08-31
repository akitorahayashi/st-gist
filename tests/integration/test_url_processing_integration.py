
import pytest

from dev.mocks.mock_ollama_client import MockOllamaApiClient
from dev.mocks.mock_scraping_service import MockScrapingService
from dev.mocks.mock_summarization_service import MockSummarizationService


class TestUrlProcessingIntegration:
    """Integration tests for URL processing workflow without external dependencies."""

    def setup_method(self):
        self.mock_ollama_client = MockOllamaApiClient()
        self.mock_scraping_service = MockScrapingService()
        self.mock_summarization_service = MockSummarizationService(
            self.mock_ollama_client
        )

    @pytest.mark.asyncio
    async def test_full_url_processing_workflow_example_com(self):
        """Test complete workflow from URL input to summary generation for example.com."""
        url = "https://example.com"

        # Step 1: Scrape content
        scraped_content = self.mock_scraping_service.scrape(url)
        assert scraped_content
        assert "Example Website" in scraped_content
        assert "technology company" in scraped_content

        # Step 2: Generate summary
        summary = await self.mock_summarization_service.summarize(scraped_content)
        assert summary
        assert "タイトル:" in summary
        assert "要点:" in summary
        assert "Exampleサイトの概要と機能紹介" in summary

    @pytest.mark.asyncio
    async def test_full_url_processing_workflow_news_site(self):
        """Test complete workflow for news website."""
        url = "https://news.example.com"

        # Step 1: Scrape content
        scraped_content = self.mock_scraping_service.scrape(url)
        assert scraped_content
        assert "Tech News Today" in scraped_content
        assert "AI Model Released" in scraped_content

        # Step 2: Generate summary
        summary = await self.mock_summarization_service.summarize(scraped_content)
        assert summary
        assert "最新技術ニュースとAI分野の動向" in summary
        assert "AI技術の進歩により" in summary

    @pytest.mark.asyncio
    async def test_full_url_processing_workflow_blog(self):
        """Test complete workflow for blog website."""
        url = "https://blog.example.com"

        # Step 1: Scrape content
        scraped_content = self.mock_scraping_service.scrape(url)
        assert scraped_content
        assert "Personal Blog" in scraped_content
        assert "Software Development" in scraped_content

        # Step 2: Generate summary
        summary = await self.mock_summarization_service.summarize(scraped_content)
        assert summary
        assert "ソフトウェア開発者の個人ブログ" in summary
        assert "フルスタック開発者による" in summary

    @pytest.mark.asyncio
    async def test_full_url_processing_workflow_unknown_url(self):
        """Test complete workflow for unknown URL."""
        url = "https://unknown-site.com"

        # Step 1: Scrape content
        scraped_content = self.mock_scraping_service.scrape(url)
        assert scraped_content
        assert "Website Content" in scraped_content
        assert "unknown-site.com" in scraped_content

        # Step 2: Generate summary
        summary = await self.mock_summarization_service.summarize(scraped_content)
        assert summary
        assert "タイトル:" in summary
        assert "要点:" in summary

    def test_scraping_error_handling(self):
        """Test error handling in scraping service."""
        # Test invalid URL
        with pytest.raises(ValueError, match="URLは http/https のみ対応しています"):
            self.mock_scraping_service.scrape("ftp://invalid.com")

        # Test blocked URL
        with pytest.raises(ValueError, match="指定のホストは許可されていません"):
            self.mock_scraping_service.scrape("https://blocked.com")

    @pytest.mark.asyncio
    async def test_summarization_with_empty_content(self):
        """Test summarization with empty content."""
        summary = await self.mock_summarization_service.summarize("")
        assert summary == ""

        summary = await self.mock_summarization_service.summarize("   ")
        assert summary == ""

    @pytest.mark.asyncio
    async def test_ollama_client_mock_responses(self):
        """Test mock Ollama client generates appropriate responses."""
        # Test custom responses
        response_parts = []
        async for chunk in self.mock_ollama_client.generate("hello"):
            response_parts.append(chunk)

        response = "".join(response_parts)
        assert "Hello! Nice to meet you!" in response

        # Test default response with context
        response_parts = []
        async for chunk in self.mock_ollama_client.generate("What is AI?"):
            response_parts.append(chunk)

        response = "".join(response_parts)
        assert "Mock response to:" in response
        assert "What is AI?" in response or "What is AI?..." in response

    @pytest.mark.asyncio
    async def test_integration_with_different_content_types(self):
        """Test integration with different types of content."""
        test_cases = [
            {
                "url": "https://example.com",
                "expected_title_keyword": "Example",
                "expected_content": "技術ソリューション",
            },
            {
                "url": "https://news.example.com",
                "expected_title_keyword": "最新技術",
                "expected_content": "AI技術",
            },
            {
                "url": "https://blog.example.com",
                "expected_title_keyword": "ソフトウェア開発者",
                "expected_content": "フルスタック開発者",
            },
        ]

        for case in test_cases:
            # Scrape and summarize
            scraped_content = self.mock_scraping_service.scrape(case["url"])
            summary = await self.mock_summarization_service.summarize(scraped_content)

            # Verify results
            assert case["expected_title_keyword"] in summary
            assert case["expected_content"] in summary
            assert len(summary.split("要点:")) == 2  # Title + bullet points
