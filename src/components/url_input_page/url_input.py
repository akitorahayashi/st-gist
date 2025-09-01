import asyncio

import streamlit as st

from src.components.think_display import (
    clear_thinking_content,
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

    # Black button with dynamic state
    if st.button(button_text, use_container_width=True, disabled=button_disabled):
        if url.strip():
            try:
                # Validate URL before processing
                scraping_service = ScrapingService()
                scraping_service.validate_url(url.strip())
                # Clear previous thinking content
                clear_thinking_content()
                # Set processing state
                st.session_state.processing = True
                st.rerun()
            except ValueError as e:
                st.session_state.last_error = f"{str(e)}"
                st.rerun()
        else:
            st.session_state.last_error = "URLを入力してください"
            st.rerun()

    # Thinking process toggle (always visible)
    st.markdown("<br>", unsafe_allow_html=True)
    show_thinking = st.toggle(
        "🤔 思考の過程を表示する",
        key="show_thinking_toggle",
        help="AIの思考過程をリアルタイムで表示します",
    )

    # Render thinking display if toggled on
    render_think_display(show_thinking)

    # Handle processing when button was clicked
    if st.session_state.get("processing", False):
        if url.strip():
            try:
                # Store URL in session state
                st.session_state.target_url = url.strip()

                # Scrape the webpage
                scraping_service = ScrapingService()
                scraped_content = scraping_service.scrape(url.strip())

                # Generate summary using existing ollama client with streaming
                if "ollama_client" in st.session_state:
                    summarization_service = SummarizationService(
                        st.session_state.ollama_client
                    )

                    # Prepare for streaming summary
                    summary_parts = []
                    clear_thinking_content()

                    # Create an async function to handle streaming
                    async def stream_summary():
                        truncated_content = scraped_content[:10000]  # Max chars
                        prompt = summarization_service._build_prompt(truncated_content)

                        chunk_count = 0
                        async for chunk in st.session_state.ollama_client.generate(
                            prompt
                        ):
                            summary_parts.append(chunk)
                            chunk_count += 1

                            # Update thinking content in real-time if toggle is on
                            if st.session_state.get("show_thinking_toggle", False):
                                thinking_complete = update_thinking_content(chunk)

                                # Trigger UI update every 10 chunks or if thinking complete
                                if chunk_count % 10 == 0 or thinking_complete:
                                    st.rerun()

                                # Check if thinking is complete and navigate to query page
                                if thinking_complete:
                                    # Short delay to show final thinking content
                                    import asyncio

                                    await asyncio.sleep(0.5)

                                    # Set navigation flag
                                    st.session_state.should_navigate_to_chat = True
                                    return "".join(summary_parts).strip()

                        return "".join(summary_parts).strip()

                    # Run the streaming summary
                    summary = asyncio.run(stream_summary())
                    st.session_state.page_summary = summary
                else:
                    st.session_state.page_summary = "要約を生成できませんでした。"

                # Reset messages for new session
                if "messages" in st.session_state:
                    st.session_state.messages = []

                # Clear processing state but don't navigate to chat yet
                # Navigation will happen when think tags are complete
                st.session_state.processing = False

                # Check if we should navigate based on thinking completion or toggle state
                should_navigate = (
                    not st.session_state.get(
                        "show_thinking_toggle", False
                    )  # Toggle is off
                    or st.session_state.get(
                        "thinking_complete", False
                    )  # Thinking is complete
                    or st.session_state.get(
                        "should_navigate_to_chat", False
                    )  # Navigation flag set
                )

                if should_navigate:
                    # Clean up navigation flag
                    if "should_navigate_to_chat" in st.session_state:
                        del st.session_state.should_navigate_to_chat
                    st.session_state.show_chat = True
                    st.rerun()

            except ValueError as e:
                st.session_state.processing = False
                st.session_state.last_error = f"エラー: {str(e)}"
                st.rerun()
            except SummarizationServiceError as e:
                st.session_state.processing = False
                st.session_state.last_error = f"要約エラー: {str(e)}"
                st.rerun()
            except Exception as e:
                st.session_state.processing = False
                st.session_state.last_error = (
                    f"予期しないエラーが発生しました: {str(e)}"
                )
                st.rerun()
        else:
            # Show error if no URL when processing started
            st.session_state.processing = False
            st.session_state.last_error = "URLを入力してください"
            st.rerun()

    # Close centered content wrapper
    st.markdown("</div>", unsafe_allow_html=True)
