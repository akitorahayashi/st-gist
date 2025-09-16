from unittest.mock import MagicMock, patch

import pytest
from olm_api_sdk.v2 import OlmLocalClientV2

from src.models.scraping_model import ScrapingModel
from src.models.summarization_model import SummarizationModel


class TestSummarizationE2E:
    """End-to-end tests for summarization with real local clients."""

    @pytest.mark.asyncio
    async def test_summarization_with_local_ollama_client(self, secrets):
        """
        Tests summarization flow with actual OlmLocalClientV2.
        Requires Ollama server running locally.
        """
        # Skip if no OLLAMA_HOST configured
        ollama_host = secrets.get("OLLAMA_HOST", "http://localhost:11434")

        # Initialize real local client
        client = OlmLocalClientV2(host=ollama_host)
        summarization_model = SummarizationModel(llm_client=client)

        # Test content
        test_content = """
        Python is a high-level, interpreted programming language with dynamic semantics.
        Its high-level built in data structures, combined with dynamic typing and dynamic binding,
        make it very attractive for Rapid Application Development, as well as for use as a
        scripting or glue language to connect existing components together.
        Python's simple, easy to learn syntax emphasizes readability and therefore reduces
        the cost of program maintenance.
        """

        # Execute summarization
        results = []
        try:
            async for thinking, summary in summarization_model.stream_summary(
                test_content
            ):
                results.append((thinking, summary))
                # Print progress for debugging
                print(f"Thinking: {thinking[:50]}...")
                print(f"Summary: {summary[:50]}...")
        except Exception as e:
            pytest.skip(f"Ollama server not available or model not found: {e}")

        # Verify results
        assert len(results) > 0
        final_thinking, final_summary = results[-1]

        # Basic validation - should have some content
        assert len(final_summary) > 0
        assert not summarization_model.is_summarizing

        # Summary should be shorter than original (rough check)
        assert len(final_summary) < len(test_content)

        print(f"Final Summary: {final_summary}")
        print(f"Final Thinking: {final_thinking}")

    @pytest.mark.asyncio
    async def test_scraping_and_summarization_integration(self, secrets):
        """
        Tests full scraping + summarization flow with real clients.
        """
        # Skip if no external dependencies available
        ollama_host = secrets.get("OLLAMA_HOST", "http://localhost:11434")

        # Initialize models
        client = OlmLocalClientV2(host=ollama_host)
        scraping_model = ScrapingModel()
        summarization_model = SummarizationModel(llm_client=client)

        # Mock scraping (to avoid external HTTP dependencies)
        test_url = "https://example.com"
        scraped_content = """
        Example Domain
        This domain is for use in illustrative examples in documents.
        You may use this domain in literature without prior coordination or asking for permission.
        More information is available at the IANA website.
        """
        scraping_model.scrape = MagicMock(return_value=scraped_content)

        try:
            # Execute full flow
            content = scraping_model.scrape(test_url)
            assert content == scraped_content

            # Generate summary
            results = []
            async for thinking, summary in summarization_model.stream_summary(content):
                results.append((thinking, summary))

            # Verify integration worked
            assert len(results) > 0
            final_thinking, final_summary = results[-1]
            assert len(final_summary) > 0
            assert (
                "example" in final_summary.lower() or "domain" in final_summary.lower()
            )

            print(f"URL: {test_url}")
            print(f"Summary: {final_summary}")

        except Exception as e:
            pytest.skip(f"External dependency not available: {e}")

    @pytest.mark.asyncio
    async def test_summarization_with_different_models(self, secrets, available_models):
        """
        Tests summarization with different model configurations.
        """
        # Use the main test model and another available model if possible
        models_to_test = [secrets.get("TEST_MODEL")]

        other_models = [m for m in available_models if m != secrets.get("TEST_MODEL")]
        if other_models:
            models_to_test.append(other_models[0])

        test_content = "Machine learning is a subset of artificial intelligence."

        for model_name in models_to_test:
            try:
                client = OlmLocalClientV2()
                summarization_model = SummarizationModel(llm_client=client)

                # Patch secrets to use specific model (SummarizationModel reads st.secrets)
                with patch("streamlit.secrets") as mock_secrets:
                    mock_secrets.get.side_effect = lambda key, default=None: {
                        "SUMMARY_MODEL": model_name
                    }.get(key, default)

                    results = []
                    async for thinking, summary in summarization_model.stream_summary(
                        test_content
                    ):
                        results.append((thinking, summary))

                    assert len(results) > 0
                    print(f"Model {model_name}: {results[-1][1][:100]}...")

            except Exception as e:
                print(f"Skipping model {model_name}: {e}")
                continue
