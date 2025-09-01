import re

import streamlit as st


def render_think_display(show_thinking: bool = False):
    """Render think tag display component"""

    if not show_thinking:
        return

    # Get current thinking content from session state
    thinking_content = st.session_state.get("current_thinking", "")
    thinking_complete = st.session_state.get("thinking_complete", False)

    if not thinking_content.strip():
        return  # Don't show anything if no content

    # Style for thinking display
    st.markdown(
        """
        <style>
        .thinking-container {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            color: #495057;
        }
        
        .thinking-header {
            font-weight: bold;
            color: #6c757d;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .thinking-content {
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display thinking content
    header_text = "🤔 AI の思考過程"
    if thinking_complete:
        header_text += " (完了 - チャットページに遷移中...)"

    st.markdown(
        f"""
        <div class="thinking-container">
            <div class="thinking-header">{header_text}</div>
            <div class="thinking-content">{thinking_content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def extract_think_content(text: str) -> tuple[str, str]:
    """
    Extract think content from text and return (thinking_content, remaining_text).

    Args:
        text: Input text that may contain <think> tags

    Returns:
        tuple of (thinking_content, text_without_think_tags)
    """
    # Pattern to match think tags and their content
    think_pattern = r"<think>(.*?)</think>"

    # Find all think content
    think_matches = re.findall(think_pattern, text, re.DOTALL)
    thinking_content = "\n".join(think_matches).strip()

    # Remove think tags from the original text
    cleaned_text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

    return thinking_content, cleaned_text


def update_thinking_content(new_chunk: str) -> bool:
    """
    Update thinking content in session state with new streaming chunk.
    This version extracts content even before the closing </think> tag appears.

    Args:
        new_chunk: New text chunk from streaming

    Returns:
        bool: True if thinking tags are complete (</think> detected)
    """
    # Initialize session state keys if they don't exist
    if "thinking_buffer" not in st.session_state:
        st.session_state["thinking_buffer"] = ""
    if "thinking_complete" not in st.session_state:
        st.session_state["thinking_complete"] = False
    if "current_thinking" not in st.session_state:
        st.session_state["current_thinking"] = ""

    st.session_state["thinking_buffer"] += new_chunk
    buffer = st.session_state["thinking_buffer"]

    # Debug: Show when we find think tags
    if "<think>" in new_chunk:
        st.write("🔍 Found <think> tag in chunk")
    if "</think>" in new_chunk:
        st.write("🔍 Found </think> tag in chunk - should complete!")

    # Extract all think content including multiple sections
    thinking_content, _ = extract_think_content(buffer)

    # Update current thinking content
    if thinking_content:
        st.session_state["current_thinking"] = thinking_content

    # Check if we have at least one complete think section
    complete_sections = buffer.count("<think>") <= buffer.count("</think>")
    has_complete_section = "<think>" in buffer and "</think>" in buffer

    if has_complete_section and complete_sections:
        st.session_state["thinking_complete"] = True
        st.write(
            f"✅ Thinking marked as complete! Buffer contains: {buffer.count('<think>')} <think> and {buffer.count('</think>')} </think>"
        )
    else:
        st.session_state["thinking_complete"] = False

    return st.session_state.get("thinking_complete", False)


def clear_thinking_content():
    """Clear thinking content from session state"""
    st.session_state["current_thinking"] = ""
    st.session_state["thinking_buffer"] = ""
    st.session_state["thinking_complete"] = False


def is_inside_think_tags(text: str) -> bool:
    """
    Check if we're currently inside think tags based on current buffer.

    Args:
        text: Current text buffer

    Returns:
        True if currently inside think tags
    """
    # Count opening and closing think tags
    open_count = text.count("<think>")
    close_count = text.count("</think>")

    return open_count > close_count
