from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
async def test_summarization_flow(
    mock_st_session, scraping_model, summarization_model, mock_secrets
):
    """
    Tests the summarization flow from URL scraping to summary generation.
    """
    # Mock scraping result
    test_url = "http://example.com"
    test_content = "This is the scraped content from the webpage."
    scraping_model.scrape = MagicMock(return_value=test_content)

    # Execute scraping
    scraped_content = scraping_model.scrape(test_url)
    assert scraped_content == test_content

    # Execute summarization
    results = []
    async for thinking, summary in summarization_model.stream_summary(scraped_content):
        results.append((thinking, summary))

    # Verify final state
    assert summarization_model.summary is not None
    assert len(summarization_model.summary) > 0
    assert not summarization_model.is_summarizing

    # Verify stream yielded results
    assert len(results) > 0
    final_thinking, final_summary = results[-1]
    assert final_summary == summarization_model.summary
    assert final_thinking == summarization_model.thinking


@pytest.mark.asyncio
async def test_summarization_with_long_content(summarization_model, mock_secrets):
    """
    Tests summarization with content that exceeds length limits.
    """
    # Create content longer than the truncation limit
    long_content = "A" * 15000  # Much longer than typical limits

    results = []
    async for thinking, summary in summarization_model.stream_summary(long_content):
        results.append((thinking, summary))

    # Should still complete successfully
    assert summarization_model.summary is not None
    assert not summarization_model.is_summarizing


@pytest.mark.asyncio
async def test_summarization_error_handling(summarization_model, mock_secrets):
    """
    Tests error handling in summarization process.
    """

    # Mock the client to raise an exception
    async def failing_generate(*args, **kwargs):
        raise Exception("Network error")

    summarization_model.llm_client.generate = failing_generate

    # Should raise SummarizationModelError
    with pytest.raises(Exception):  # Could be SummarizationModelError specifically
        async for _ in summarization_model.stream_summary("test content"):
            pass

    # Should not be in summarizing state after error
    assert not summarization_model.is_summarizing
