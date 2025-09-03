from string import Template
from unittest.mock import MagicMock, mock_open, patch

import pytest

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
    def test_load_summarization_prompt_template_success(self, summarization_model):
        """Test that the summarization prompt template is loaded correctly."""
        mock_template_content = "Template: $content"
        target_path = "src/static/prompts/summarization_prompt.md"

        with patch(
            "builtins.open", mock_open(read_data=mock_template_content)
        ) as mock_file:
            with patch(
                "src.models.summarization_model.os.path.join", return_value=target_path
            ):
                template = summarization_model._load_summarization_prompt_template()

                mock_file.assert_called_once_with(target_path, "r", encoding="utf-8")
                assert isinstance(template, Template)
                assert template.template == mock_template_content

    def test_load_summarization_prompt_template_file_not_found(
        self, summarization_model
    ):
        """Test that FileNotFoundError is raised when the template file is not found."""
        target_path = "src/static/prompts/summarization_prompt.md"

        with patch("builtins.open", side_effect=FileNotFoundError) as mock_file:
            with patch(
                "src.models.summarization_model.os.path.join", return_value=target_path
            ):
                with pytest.raises(FileNotFoundError):
                    summarization_model._load_summarization_prompt_template()
                mock_file.assert_called_once_with(target_path, "r", encoding="utf-8")

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

        results = []
        async for thinking, summary in summarization_model.stream_summary(
            scraped_content
        ):
            results.append((thinking, summary))

        # Check intermediate yields based on the updated extract_think_content logic
        # 1st yield: "<think>Thinking " - Incomplete tag, extract "Thinking " as thinking content
        assert results[0] == ("Thinking", "")
        # 2nd yield: "<think>Thinking about it.</think>" - Complete tag, extract "Thinking about it." as thinking
        assert results[1] == ("Thinking about it.", "")
        # 3rd yield: "<think>Thinking about it.</think>This is the summary." - Complete tag + summary
        assert results[2] == ("Thinking about it.", "This is the summary.")
        # Final yield from the completed stream
        assert results[3] == ("Thinking about it.", "This is the summary.")

        # Check final state
        assert summarization_model.thinking == "Thinking about it."
        assert summarization_model.summary == "This is the summary."
        assert not summarization_model.is_summarizing

    @pytest.mark.asyncio
    async def test_stream_summary_llm_error(self, summarization_model, mock_llm_client):
        """Test that stream_summary handles errors from the LLM client."""
        scraped_content = "This is some content."

        async def error_generator():
            yield "this is fine"
            raise Exception("LLM Error")

        mock_llm_client.generate.return_value = error_generator()

        with patch("streamlit.session_state", MagicMock()):
            with pytest.raises(
                SummarizationModelError,
                match="要約のストリーミング生成に失敗しました。",
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
