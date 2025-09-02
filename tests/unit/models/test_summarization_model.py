import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from src.models.summarization_model import SummarizationModel, SummarizationModelError


@pytest.fixture
def mock_llm_client():
    """Fixture for a mocked LLM client."""
    # The client method `generate` is sync but returns an async generator,
    # so the mock itself should not be async.
    return MagicMock()


@pytest.fixture
def summarization_model(mock_llm_client):
    """Fixture for a SummarizationModel instance."""
    return SummarizationModel(llm_client=mock_llm_client)


class TestSummarizationModel:
    def test_build_prompt(self, summarization_model):
        """Test that _build_prompt creates the correct prompt string."""
        text = "This is a test content."
        prompt = summarization_model._build_prompt(text)
        assert "以下のテキストを日本語で要約してください。" in prompt
        assert f"テキスト:\n{text}" in prompt
        assert "タイトル:" in prompt
        assert "要点:" in prompt

    @pytest.mark.asyncio
    async def test_stream_summary_success(self, summarization_model, mock_llm_client):
        """Test successful streaming summarization."""
        scraped_content = "This is the content to be summarized."

        # This should be an async generator
        async def stream_generator():
            yield "<think>Thinking "
            yield "about it.</think>"
            yield "This is the summary."

        # The mock's return value should be the async generator itself
        mock_llm_client.generate.return_value = stream_generator()

        # Mock streamlit session state
        with patch("streamlit.session_state", MagicMock()) as mock_st_session_state:
            # Mock conversation_service on session_state
            mock_conv_service = MagicMock()
            mock_conv_service.extract_think_content.return_value = (
                "Thinking about it.",
                "This is the summary.",
            )
            mock_st_session_state.get.return_value = mock_conv_service
            mock_st_session_state.__contains__.return_value = True

            results = []
            async for thinking, summary in summarization_model.stream_summary(
                scraped_content
            ):
                results.append((thinking, summary))

            # Check intermediate yields
            assert results[0] == ("Thinking ", "")  # After first chunk
            assert results[1] == ("Thinking about it.", "")  # After second chunk
            assert results[2] == (
                "Thinking about it.",
                "This is the summary.",
            )  # After third chunk

            # Check final state
            assert summarization_model.thinking == "Thinking about it."
            assert summarization_model.summary == "This is the summary."
            assert not summarization_model.is_summarizing

    @pytest.mark.asyncio
    async def test_stream_summary_llm_error(
        self, summarization_model, mock_llm_client
    ):
        """Test that stream_summary handles errors from the LLM client."""
        scraped_content = "This is some content."

        async def error_generator():
            yield "this is fine"
            raise Exception("LLM Error")

        mock_llm_client.generate.return_value = error_generator()

        with patch("streamlit.session_state", MagicMock()):
            with pytest.raises(
                SummarizationModelError, match="要約のストリーミング生成に失敗しました。"
            ):
                async for _ in summarization_model.stream_summary(scraped_content):
                    pass

        assert not summarization_model.is_summarizing

    def test_reset(self, summarization_model):
        """Test that the reset method clears the state."""
        summarization_model.summary = "A summary"
        summarization_model.thinking = "Some thoughts"
        summarization_model.is_summarizing = True

        summarization_model.reset()

        assert summarization_model.summary == ""
        assert summarization_model.thinking == ""
        assert not summarization_model.is_summarizing
