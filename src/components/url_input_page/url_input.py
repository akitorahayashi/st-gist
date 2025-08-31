import asyncio

import streamlit as st

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

    st.markdown("<br>", unsafe_allow_html=True)

    # Check if processing
    is_processing = st.session_state.get("processing", False)

    # Dynamic button text and state
    button_text = "要約中..." if is_processing else "要約を開始"
    button_disabled = is_processing

    # Black button with dynamic state
    if st.button(button_text, use_container_width=True, disabled=button_disabled):
        if url.strip():
            # Set processing state
            st.session_state.processing = True
            st.rerun()

    # Handle processing when button was clicked
    if st.session_state.get("processing", False):
        if url.strip():
            try:
                # Store URL in session state
                st.session_state.target_url = url.strip()

                # Scrape the webpage
                scraping_service = ScrapingService()
                scraped_content = scraping_service.scrape(url.strip())

                # Generate summary using existing ollama client
                if "ollama_client" in st.session_state:
                    summarization_service = SummarizationService(
                        st.session_state.ollama_client
                    )
                    summary = asyncio.run(summarization_service.summarize(scraped_content))
                    st.session_state.page_summary = summary
                else:
                    st.session_state.page_summary = "要約を生成できませんでした。"

                # Reset messages for new session
                if "messages" in st.session_state:
                    st.session_state.messages = []

                # Clear processing state and navigate to chat
                st.session_state.processing = False
                st.session_state.show_chat = True
                st.rerun()

            except ValueError as e:
                st.session_state.processing = False
                st.error(f"エラー: {str(e)}")
                st.rerun()
            except SummarizationServiceError as e:
                st.session_state.processing = False
                st.error(f"要約エラー: {str(e)}")
                st.rerun()
            except Exception as e:
                st.session_state.processing = False
                st.error(f"予期しないエラーが発生しました: {str(e)}")
                st.rerun()
        else:
            # Show error if no URL when processing started
            st.session_state.processing = False
            st.error("URLを入力してください")
            st.rerun()

    # Close centered content wrapper
    st.markdown("</div>", unsafe_allow_html=True)
