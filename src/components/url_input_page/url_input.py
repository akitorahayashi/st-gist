import streamlit as st

from src.services.scraping_service import ScrapingService


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
    placeholder = st.empty()
    with placeholder.container():
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
        button_text = "ページの内容を取得中..." if is_processing else "要約を開始"
        button_disabled = is_processing

        st.markdown("<br>", unsafe_allow_html=True)

        # Button click to start scraping process
        if st.button(button_text, use_container_width=True, disabled=button_disabled):
            if url.strip():
                try:
                    # Validate URL and start scraping
                    ScrapingService().validate_url(url.strip())
                    st.session_state.processing = True
                    st.session_state.target_url = url.strip()
                    st.rerun()
                except ValueError as e:
                    st.session_state.last_error = f"{str(e)}"
                    st.rerun()
            else:
                st.session_state.last_error = "URLを入力してください"
                st.rerun()

    # Processing: scrape and store content, then transition
    if is_processing:
        try:
            # Perform scraping with validation
            scraped_content = ScrapingService().scrape(
                st.session_state.target_url
            )
            st.session_state.scraped_content = scraped_content

            # Clean up processing state
            st.session_state.processing = False
            st.session_state.pop("target_url", None)

            # Reset messages for new session
            if "messages" in st.session_state:
                st.session_state.messages = []

            # Clear the placeholder and navigate to Query Page
            placeholder.empty()
            st.session_state.show_chat = True
            st.rerun()

        except (ValueError, Exception) as e:
            st.session_state.processing = False
            st.session_state.last_error = f"エラーが発生しました: {str(e)}"
            st.rerun()

    # Close centered content wrapper
    st.markdown("</div>", unsafe_allow_html=True)