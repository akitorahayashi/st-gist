from unittest.mock import Mock

import pytest

from src.services.summarization_service import (
    SummarizationService,
    SummarizationServiceError,
)


class TestSummarizationService:

    def setup_method(self):
        self.mock_llm_client = Mock()
        self.summarization_service = SummarizationService(self.mock_llm_client)

    @pytest.mark.asyncio
    async def test_summarize_empty_text(self):
        """Test summarization with empty text."""
        result = await self.summarization_service.summarize("")
        assert result == ""

        result = await self.summarization_service.summarize("   ")
        assert result == ""

    @pytest.mark.asyncio
    async def test_summarize_success(self):
        """Test successful summarization."""

        # Mock the async generator
        async def mock_generate(prompt):
            yield "タイトル: テスト記事"
            yield "\n\n要点:\n• ポイント1"
            yield "\n• ポイント2"

        self.mock_llm_client.generate = mock_generate

        result = await self.summarization_service.summarize("Test content")

        expected = "タイトル: テスト記事\n\n要点:\n• ポイント1\n• ポイント2"
        assert result == expected

    @pytest.mark.asyncio
    async def test_summarize_with_max_chars(self):
        """Test summarization with character limit."""
        long_text = "a" * 20000

        async def mock_generate(prompt):
            # Verify the text was truncated
            assert len(prompt.split("テキスト:\n")[1].split("\n\n要約は")[0]) == 5000
            yield "要約結果"

        self.mock_llm_client.generate = mock_generate

        result = await self.summarization_service.summarize(long_text, max_chars=5000)
        assert result == "要約結果"

    @pytest.mark.asyncio
    async def test_summarize_llm_client_exception(self):
        """Test summarization with LLM client exception."""

        async def mock_generate(prompt):
            if False:  # Make this a proper async generator that raises
                yield ""
            raise Exception("API Error")

        self.mock_llm_client.generate = mock_generate

        with pytest.raises(SummarizationServiceError, match="要約の生成に失敗しました"):
            await self.summarization_service.summarize("Test content")

    def test_build_prompt(self):
        """Test prompt building."""
        text = "Sample text content"
        prompt = self.summarization_service._build_prompt(text)

        assert "以下のテキストを日本語で要約してください" in prompt
        assert "Sample text content" in prompt
        assert "タイトル:" in prompt
        assert "要点:" in prompt

    @pytest.mark.asyncio
    async def test_summarize_strips_whitespace(self):
        """Test that summarization strips whitespace from result."""

        async def mock_generate(prompt):
            yield "  \n  要約結果  \n  "

        self.mock_llm_client.generate = mock_generate

        result = await self.summarization_service.summarize("Test content")
        assert result == "要約結果"
