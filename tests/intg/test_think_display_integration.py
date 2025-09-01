import pytest

from src.components.think_display import (
    clear_thinking_content,
    extract_think_content,
    is_inside_think_tags,
    render_think_display,
    update_thinking_content,
)


class MockSessionState:
    """Mock Streamlit session state for testing"""

    def __init__(self):
        self._state = {}

    def get(self, key, default=None):
        return self._state.get(key, default)

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self._state[key] = value

    def __contains__(self, key):
        return key in self._state


@pytest.fixture
def mock_session_state(monkeypatch):
    """Mock streamlit session state"""
    mock_state = MockSessionState()

    # Mock the streamlit module
    class MockST:
        def __init__(self):
            self.session_state = mock_state

        def markdown(self, content, unsafe_allow_html=False):
            pass  # No-op for testing

    mock_st = MockST()
    monkeypatch.setattr("src.components.think_display.st", mock_st)

    return mock_state


class TestThinkDisplayIntegration:
    """Integration tests for think display functionality"""

    def test_extract_think_content_simple(self):
        """Test basic think content extraction"""
        text = "<think>This is a thought</think>Hello world"
        thinking, remaining = extract_think_content(text)

        assert thinking == "This is a thought"
        assert remaining == "Hello world"

    def test_extract_think_content_multiple(self):
        """Test multiple think tags extraction"""
        text = "<think>First thought</think>Some text<think>Second thought</think>More text"
        thinking, remaining = extract_think_content(text)

        assert "First thought" in thinking
        assert "Second thought" in thinking
        assert remaining == "Some textMore text"

    def test_extract_think_content_multiline(self):
        """Test multiline think content extraction"""
        text = """<think>
This is a
multiline thought
</think>

Regular content here"""
        thinking, remaining = extract_think_content(text)

        assert "multiline thought" in thinking
        assert "Regular content here" in remaining

    def test_update_thinking_content_incremental(self, mock_session_state):
        """Test incremental updating of thinking content"""
        clear_thinking_content()

        # Simulate streaming chunks
        chunks = ["<think>", "This ", "is ", "a ", "thought", "</think>", "End"]

        for i, chunk in enumerate(chunks):
            complete = update_thinking_content(chunk)

            if i < len(chunks) - 2:  # Before </think>
                assert not complete
            else:  # After </think>
                assert complete

        # Check final state
        assert mock_session_state.get("current_thinking") == "This is a thought"
        assert mock_session_state.get("thinking_complete")

    def test_update_thinking_content_incomplete(self, mock_session_state):
        """Test updating with incomplete think tags"""
        clear_thinking_content()

        # Only opening tag
        complete = update_thinking_content("<think>Partial thought")

        assert not complete
        assert not mock_session_state.get("thinking_complete", False)

    def test_is_inside_think_tags(self):
        """Test detection of being inside think tags"""

        # No tags
        assert not is_inside_think_tags("Just text")

        # Opening tag only
        assert is_inside_think_tags("<think>Inside")

        # Complete tag pair
        assert not is_inside_think_tags("<think>Complete</think>")

        # Multiple opening, one closing
        assert is_inside_think_tags("<think>First<think>Second</think>")

        # Equal opening and closing
        assert not is_inside_think_tags("<think>One</think><think>Two</think>")

    def test_clear_thinking_content(self, mock_session_state):
        """Test clearing thinking content"""
        # Set some state
        mock_session_state["current_thinking"] = "Some thought"
        mock_session_state["thinking_buffer"] = "Some buffer"
        mock_session_state["thinking_complete"] = True

        clear_thinking_content()

        assert mock_session_state.get("current_thinking") == ""
        assert mock_session_state.get("thinking_buffer") == ""
        assert not mock_session_state.get("thinking_complete")

    def test_render_think_display_no_content(self, mock_session_state):
        """Test rendering with no thinking content"""
        clear_thinking_content()

        # Should not render anything when no content
        render_think_display(show_thinking=True)
        # No assertion needed - just ensure it doesn't crash

    def test_render_think_display_with_content(self, mock_session_state):
        """Test rendering with thinking content"""
        mock_session_state["current_thinking"] = "This is a test thought"

        # Should render content when available
        render_think_display(show_thinking=True)
        # No assertion needed - just ensure it doesn't crash

    def test_render_think_display_toggle_off(self, mock_session_state):
        """Test rendering when toggle is off"""
        mock_session_state["current_thinking"] = "This should not be shown"

        # Should not render when toggle is off
        render_think_display(show_thinking=False)
        # No assertion needed - just ensure it doesn't crash

    def test_full_workflow_simulation(self, mock_session_state):
        """Test complete workflow from start to finish"""
        # Start clean
        clear_thinking_content()

        # Simulate mock ollama response with think tags
        mock_response = "<think>Let me analyze this URL. It seems to be a website about technology.</think>Here's my summary: This is a technology website."

        # Process in chunks (simulating streaming)
        chunks = []
        for i in range(0, len(mock_response), 5):  # 5-char chunks
            chunks.append(mock_response[i : i + 5])

        thinking_complete = False
        for chunk in chunks:
            thinking_complete = update_thinking_content(chunk)

            if thinking_complete:
                break

        # Verify final state
        assert thinking_complete
        assert mock_session_state.get("thinking_complete")
        expected_thinking = (
            "Let me analyze this URL. It seems to be a website about technology."
        )
        assert mock_session_state.get("current_thinking") == expected_thinking

    def test_malformed_think_tags(self, mock_session_state):
        """Test handling of malformed think tags"""
        clear_thinking_content()

        # Missing closing tag
        update_thinking_content("<think>Unclosed thought")
        thinking, _ = extract_think_content(
            mock_session_state.get("thinking_buffer", "")
        )
        assert thinking == ""  # Should be empty for incomplete tags

        # Extra closing tag
        update_thinking_content("</think>Extra close")
        # Should not crash

    def test_nested_think_tags(self, mock_session_state):
        """Test handling of nested think tags (should not happen but test anyway)"""
        clear_thinking_content()

        text = "<think>Outer <think>Inner</think> thought</think>"
        thinking, remaining = extract_think_content(text)

        # Should extract the outer content
        assert "Outer" in thinking and "thought" in thinking
        assert remaining == ""

    def test_performance_with_large_buffer(self, mock_session_state):
        """Test performance with large thinking buffer"""
        clear_thinking_content()

        # Create a large thinking content
        large_thought = "This is a very long thought. " * 1000
        large_response = f"<think>{large_thought}</think>Summary here"

        # Process in chunks
        chunks = [
            large_response[i : i + 100] for i in range(0, len(large_response), 100)
        ]

        for chunk in chunks:
            complete = update_thinking_content(chunk)
            if complete:
                break

        # Verify it worked with large content
        assert mock_session_state.get("thinking_complete")
        assert len(mock_session_state.get("current_thinking", "")) > 1000
