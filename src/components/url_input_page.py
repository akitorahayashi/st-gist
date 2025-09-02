import streamlit as st

from src.services.scraping_service import ScrapingService

def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    app_state = st.session_state.app_state

    # st.containerを使用してセクションをグループ化
    with st.container():
        render_app_description()
        render_url_input_form()

def render_app_description():
    """Render app description with left-aligned layout"""
    st.markdown(
        """
        <style>
        .app-description h2 {
            color: #333;
            margin-bottom: 1rem;
            font-size: 1.8rem;
        }
        .app-description p {
            color: #666;
            font-size: 1.1rem;
            line-height: 1.5;
            margin-bottom: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="app-description">
            <h2>ウェブページ要約ツール</h2>
            <p>
                URLを入力することで、AIがページの内容を分析・要約し、<br>
                そのページについて質問できるチャットボットになります
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
from src.services.scraping_service import ScrapingService


def render_url_input_form():
    """Render URL input form with centered layout"""
    app_state = st.session_state.app_state

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

    with st.container():
        url = st.text_input(
            "URLを入力してください",
            placeholder="https://example.com",
            key="url_input",
            label_visibility="collapsed",
            disabled=app_state.is_processing,
        )

        if app_state.last_error:
            st.error(app_state.last_error)
            app_state.clear_error()

        st.markdown("<br>", unsafe_allow_html=True)

        button_text = (
            "ページの内容を取得中..." if app_state.is_processing else "要約を開始"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            button_text, use_container_width=True, disabled=app_state.is_processing
        ):
            if url.strip():
                try:
                    ScrapingService().validate_url(url.strip())
                    app_state.start_summarization(url.strip())
                    scraped_content = ScrapingService().scrape(url.strip())
                    app_state.complete_summarization(scraped_content)
                    st.rerun()
                except ValueError as e:
                    app_state.set_error(f"{str(e)}")
                    st.rerun()
                except Exception as e:
                    app_state.set_error(f"エラーが発生しました: {str(e)}")
                    st.rerun()
            else:
                app_state.set_error("URLを入力してください")
                st.rerun()
