from unittest.mock import patch

import pytest

from dev.mocks.mock_ollama_client import MockOllamaApiClient
from dev.mocks.mock_scraping_service import MockScrapingService
from src.components.think_display import clear_thinking_content, update_thinking_content
from src.services.summarization_service import SummarizationService


class MockSessionState:
    """Mock Streamlit session state for testing"""

    def __init__(self):
        self._state = {
            "show_thinking_toggle": True,  # Default to on for testing
            "processing": False,
            "show_chat": False,
        }

    def get(self, key, default=None):
        return self._state.get(key, default)

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self._state[key] = value

    def __contains__(self, key):
        return key in self._state

    def pop(self, key, default=None):
        return self._state.pop(key, default)


class TestUrlProcessingWithThinkingIntegration:
    """Integration tests for URL processing with thinking display functionality"""

    @pytest.fixture
    def mock_session_state(self):
        return MockSessionState()

    @pytest.fixture
    def mock_ollama_client(self):
        return MockOllamaApiClient()

    @pytest.fixture
    def mock_scraping_service(self):
        return MockScrapingService()

    @pytest.fixture
    def summarization_service(self, mock_ollama_client):
        return SummarizationService(mock_ollama_client)

    def test_thinking_content_extraction_during_summarization(
        self, mock_session_state, summarization_service
    ):
        """Test that thinking content is properly extracted during summarization"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            # Clear any previous thinking content
            clear_thinking_content()

            # Create a test response that includes think tags
            test_response = "<think>Let me analyze this content carefully.</think>Here is the summary."

            # Simulate chunk-by-chunk processing
            chunks = [test_response[i : i + 5] for i in range(0, len(test_response), 5)]

            thinking_complete = False
            for chunk in chunks:
                thinking_complete = update_thinking_content(chunk)
                if thinking_complete:
                    break

            # Verify thinking content was extracted
            assert mock_session_state.get("thinking_complete")
            assert "Let me analyze this content carefully." in mock_session_state.get(
                "current_thinking", ""
            )

    def test_page_navigation_after_thinking_complete(self, mock_session_state):
        """Test that page navigation logic works correctly after thinking completion"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            # Setup initial state
            mock_session_state["show_thinking_toggle"] = True
            mock_session_state["processing"] = True
            mock_session_state["show_chat"] = False
            clear_thinking_content()

            # Simulate thinking completion
            test_response = "<think>Analysis complete</think>Summary ready"

            thinking_complete = False
            for chunk in [
                test_response[i : i + 3] for i in range(0, len(test_response), 3)
            ]:
                thinking_complete = update_thinking_content(chunk)
                if thinking_complete:
                    break

            # Check navigation logic
            assert thinking_complete
            assert mock_session_state.get("thinking_complete")

            # Simulate the navigation check logic from url_input.py
            should_navigate = (
                not mock_session_state.get(
                    "show_thinking_toggle", False
                )  # Toggle is off
                or mock_session_state.get(
                    "thinking_complete", False
                )  # Thinking is complete
                or mock_session_state.get(
                    "should_navigate_to_chat", False
                )  # Navigation flag set
            )

            assert should_navigate

    def test_no_navigation_when_thinking_incomplete(self, mock_session_state):
        """Test that navigation doesn't happen when thinking is incomplete"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            # Setup initial state
            mock_session_state["show_thinking_toggle"] = True
            mock_session_state["processing"] = True
            mock_session_state["show_chat"] = False
            clear_thinking_content()

            # Simulate incomplete thinking (no closing tag)
            incomplete_response = "<think>Still thinking about this..."

            thinking_complete = update_thinking_content(incomplete_response)

            # Check that thinking is not complete
            assert not thinking_complete
            assert not mock_session_state.get("thinking_complete", False)

            # Simulate the navigation check logic
            should_navigate = (
                not mock_session_state.get("show_thinking_toggle", False)
                or mock_session_state.get("thinking_complete", False)
                or mock_session_state.get("should_navigate_to_chat", False)
            )

            assert not should_navigate

    def test_navigation_when_toggle_off(self, mock_session_state):
        """Test that navigation happens immediately when thinking toggle is off"""
        # Setup state with toggle off
        mock_session_state["show_thinking_toggle"] = False
        mock_session_state["processing"] = True
        mock_session_state["show_chat"] = False

        # Simulate the navigation check logic
        should_navigate = (
            not mock_session_state.get("show_thinking_toggle", False)
            or mock_session_state.get("thinking_complete", False)
            or mock_session_state.get("should_navigate_to_chat", False)
        )

        # Should navigate immediately since toggle is off
        assert should_navigate

    @pytest.mark.asyncio
    async def test_full_workflow_with_mock_client(
        self, mock_session_state, mock_ollama_client, mock_scraping_service
    ):
        """Test complete workflow from URL input to thinking completion"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            # Setup
            url = "https://example.com"
            mock_session_state["show_thinking_toggle"] = True
            clear_thinking_content()

            # Step 1: Scrape content
            scraped_content = mock_scraping_service.scrape(url)
            assert "Example Website" in scraped_content

            # Step 2: Create summarization service
            summarization_service = SummarizationService(mock_ollama_client)

            # Step 3: Simulate the streaming summarization process
            truncated_content = scraped_content[:10000]
            prompt = summarization_service._build_prompt(truncated_content)

            # Collect all chunks and process thinking
            summary_parts = []
            thinking_complete = False

            async for chunk in mock_ollama_client.generate(prompt):
                summary_parts.append(chunk)

                # Simulate the thinking processing from url_input.py
                if mock_session_state.get("show_thinking_toggle", False):
                    thinking_complete = update_thinking_content(chunk)

                    if thinking_complete:
                        # Simulate the early return when thinking is complete
                        mock_session_state["should_navigate_to_chat"] = True
                        break

            # Verify the workflow
            summary = "".join(summary_parts).strip()
            assert len(summary) > 0
            assert thinking_complete
            assert mock_session_state.get("thinking_complete")
            assert mock_session_state.get("should_navigate_to_chat")

    def test_thinking_content_persistence_across_chunks(self, mock_session_state):
        """Test that thinking content persists and accumulates across chunks"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            clear_thinking_content()

            # Simulate streaming chunks that build up thinking content
            chunks = [
                "<think>",
                "First I need to understand the context. ",
                "Then I should analyze the main points. ",
                "Finally, I'll create a comprehensive summary.",
                "</think>",
                "Here's my analysis...",
            ]

            thinking_states = []
            for chunk in chunks:
                complete = update_thinking_content(chunk)
                current_thinking = mock_session_state.get("current_thinking", "")
                thinking_states.append(
                    {"chunk": chunk, "complete": complete, "thinking": current_thinking}
                )

            # Verify progression
            assert not thinking_states[0]["complete"]  # "<think>"
            assert not thinking_states[1]["complete"]  # First sentence
            assert not thinking_states[2]["complete"]  # Second sentence
            assert not thinking_states[3]["complete"]  # Third sentence
            assert thinking_states[4]["complete"]  # "</think>"

            # Final thinking should contain all content
            final_thinking = thinking_states[-1]["thinking"]
            assert "understand the context" in final_thinking
            assert "analyze the main points" in final_thinking
            assert "comprehensive summary" in final_thinking

    def test_error_handling_with_malformed_chunks(self, mock_session_state):
        """Test error handling when chunks contain malformed content"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            clear_thinking_content()

            # Test with various malformed inputs
            malformed_chunks = [
                "<think",  # Incomplete opening tag
                ">>corrupted<<",  # Random characters
                "</think",  # Incomplete closing tag
                "normal text",  # Regular text
            ]

            # Should not crash with any of these
            for chunk in malformed_chunks:
                try:
                    update_thinking_content(chunk)
                except Exception as e:
                    pytest.fail(
                        f"update_thinking_content crashed with chunk '{chunk}': {e}"
                    )

    def test_multiple_think_sections_in_response(self, mock_session_state):
        """Test handling of multiple think sections in a single response"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            clear_thinking_content()

            # Response with multiple think sections
            complex_response = """<think>First analysis step</think>
            Intermediate result.
            <think>Second analysis step</think>
            Final conclusion."""

            # Process in chunks
            chunks = [
                complex_response[i : i + 10]
                for i in range(0, len(complex_response), 10)
            ]

            for chunk in chunks:
                update_thinking_content(chunk)

            # Should extract all thinking content
            final_thinking = mock_session_state.get("current_thinking", "")
            assert "First analysis step" in final_thinking
            assert "Second analysis step" in final_thinking

    def test_state_cleanup_on_new_session(self, mock_session_state):
        """Test that thinking state is properly cleaned up for new sessions"""
        with patch("src.components.think_display.st") as mock_st:
            mock_st.session_state = mock_session_state

            # Set up some existing state
            mock_session_state["current_thinking"] = "Old thinking"
            mock_session_state["thinking_buffer"] = "Old buffer"
            mock_session_state["thinking_complete"] = True

            # Clear for new session
            clear_thinking_content()

            # Verify cleanup
            assert mock_session_state.get("current_thinking") == ""
            assert mock_session_state.get("thinking_buffer") == ""
            assert not mock_session_state.get("thinking_complete")
