import asyncio

import streamlit as st

from src.components.think_display import (
    clear_thinking_content,
    extract_think_content,
    render_think_display,
    update_thinking_content,
)
from src.services.scraping_service import ScrapingService
from src.services.summarization_service import (
    SummarizationService,
    SummarizationServiceError,
)


def render_url_input_form():
    """Render URL input form with centered layout"""

    # Hide sidebar for URL input page and add responsive styling
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* Override Streamlit's default layout */
        .main .block-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            height: 100vh;
            overflow: hidden;
            padding: 0;
            padding-bottom: 4rem !important;
            margin: 0 auto;
            max-width: 600px;
        }
        
        /* Create centered content wrapper */
        .centered-content {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            padding: 2rem;
            box-sizing: border-box;
        }
        
        /* Responsive input styling */
        .stTextInput > div > div > input {
            text-align: center;
            font-size: 1.1rem;
            padding: 0.8rem;
        }
        
        /* Black button styling */
        .stButton > button {
            width: 100%;
            background-color: #000000 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.8rem 2rem !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            background-color: #333333 !important;
            color: white !important;
            border: none !important;
        }
        
        .stButton > button:focus {
            background-color: #000000 !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 0 0 2px #666666 !important;
        }
        
        /* Processing button state */
        .stButton > button:disabled {
            background-color: #333333 !important;
            color: white !important;
            cursor: not-allowed !important;
            opacity: 0.8 !important;
        }
        
        /* Ensure disabled state overrides other styles */
        .stButton > button[disabled] {
            background-color: #333333 !important;
            color: white !important;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main .block-container {
                max-width: 90%;
            }
            .centered-content {
                padding: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create centered content wrapper
    st.markdown('<div class="centered-content">', unsafe_allow_html=True)

    # URL input and button - truly centered
    url = st.text_input(
        "URLを入力してください",
        placeholder="https://example.com",
        key="url_input",
        label_visibility="collapsed",
    )

    # Show error message directly under the input
    last_error = st.session_state.pop("last_error", None)
    if last_error:
        st.error(last_error)

    st.markdown("<br>", unsafe_allow_html=True)

    # Check if processing
    is_processing = st.session_state.get("processing", False)

    # Dynamic button text and state
    button_text = "要約中..." if is_processing else "要約を開始"
    button_disabled = is_processing

    # Thinking process toggle (always visible)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Store current toggle state separately to avoid iterator conflicts
    current_show_thinking = st.session_state.get("show_thinking_toggle", False)
    show_thinking = st.toggle(
        "🤔 思考の過程を表示する",
        key="show_thinking_toggle",
        help="AIの思考過程をリアルタイムで表示します",
    )
    
    # Update thinking display state only if changed and not processing
    if not is_processing and current_show_thinking != show_thinking:
        st.session_state["show_thinking_display"] = show_thinking
    elif is_processing:
        # During processing, use the stored display state
        show_thinking = st.session_state.get("show_thinking_display", show_thinking)

    # Placeholder for real-time thinking display
    thinking_placeholder = st.empty()

    # --- NEW ARCHITECTURE ---

    # Step 1: Button click to start the whole process
    if st.button(button_text, use_container_width=True, disabled=button_disabled):
        if url.strip():
            try:
                # Validate URL and set initial state
                ScrapingService().validate_url(url.strip())
                clear_thinking_content()
                st.session_state.processing = True
                st.session_state.target_url = url.strip()
                st.session_state.processing_step = "scrape"  # Start with scraping
                st.rerun()
            except ValueError as e:
                st.session_state.last_error = f"{str(e)}"
                st.rerun()
        else:
            st.session_state.last_error = "URLを入力してください"
            st.rerun()

    # Main processing block, driven by session state
    if is_processing:
        step = st.session_state.get("processing_step")

        try:
            if step == "scrape":
                with st.spinner("ウェブページを読み込んでいます..."):
                    st.session_state.scraped_content = ScrapingService().scrape(
                        st.session_state.target_url
                    )
                st.session_state.processing_step = "summarize_init"
                st.rerun()

            elif step == "summarize_init":
                if "ollama_client" in st.session_state:
                    summarization_service = SummarizationService(
                        st.session_state.ollama_client
                    )
                    truncated_content = st.session_state.scraped_content[:10000]
                    prompt = summarization_service._build_prompt(truncated_content)

                    st.session_state.summary_iterator = (
                        st.session_state.ollama_client.generate(prompt)
                    )
                    st.session_state.summary_parts = []
                    st.session_state.processing_step = "summarize_streaming"
                    st.rerun()
                else:
                    raise SummarizationServiceError("Ollama client not found.")

            elif step == "summarize_streaming":
                # Display thinking container if toggled
                if show_thinking:
                    with thinking_placeholder.container():
                        render_think_display(True)

                try:
                    # Get or create the event loop for the current thread
                    loop = asyncio.get_running_loop()
                except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                try:
                    chunk = loop.run_until_complete(
                        st.session_state.summary_iterator.__anext__()
                    )
                    st.session_state.summary_parts.append(chunk)

                    # Update thinking content for display
                    if show_thinking:
                        thinking_complete = update_thinking_content(chunk)
                        
                        # Check if thinking is complete - navigate when thinking ends
                        if thinking_complete:
                            st.session_state.processing_step = "summarize_finish"
                            st.rerun()
                            return

                    # Show current accumulated response
                    accumulated_text = ''.join(st.session_state.summary_parts)
                    st.write("**Current Response:**")
                    st.write(accumulated_text)

                    # Continue with next chunk
                    st.rerun()

                except StopAsyncIteration:
                    # Stream ended, finish processing (fallback if thinking didn't complete)
                    st.session_state.processing_step = "summarize_finish"
                    st.rerun()

            elif step == "summarize_finish":
                summary_with_tags = "".join(st.session_state.summary_parts)
                thinking_content, cleaned_summary = extract_think_content(summary_with_tags)
                
                # Store both thinking and summary content for Query Page
                st.session_state.page_summary = cleaned_summary
                if thinking_content.strip():
                    st.session_state.current_thinking = thinking_content

                # Reset session for the chat page
                if "messages" in st.session_state:
                    st.session_state.messages = []

                # Clean up processing state (but keep thinking content)
                keys_to_delete = [
                    "processing",
                    "processing_step", 
                    "target_url",
                    "scraped_content",
                    "summary_iterator",
                    "summary_parts",
                    "thinking_buffer",  # Clean up buffer but keep current_thinking
                    "thinking_complete",
                ]
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]

                # Navigate to chat page
                st.session_state.show_chat = True
                st.rerun()

        except (ValueError, SummarizationServiceError, Exception) as e:
            st.session_state.processing = False
            st.session_state.last_error = f"エラーが発生しました: {str(e)}"
            # Clean up potentially problematic state
            st.session_state.pop("processing_step", None)
            st.rerun()

    # Close centered content wrapper
    st.markdown("</div>", unsafe_allow_html=True)
