import streamlit as st
import time
import asyncio
from src.services.scraping_service import ScrapingService
from src.services.summarization_service import SummarizationService, SummarizationServiceError
from src.components.header import render_header
from src.components.footer import render_footer


def render_url_input_page():
    """Render URL input page with centered layout"""
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
            min-height: calc(100vh - 6rem);
            padding-top: 6rem;
            padding-bottom: 2rem;
            max-width: 600px;
            margin: 0 auto;
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
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main .block-container {
                padding-top: 5rem;
                max-width: 90%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header component
    render_header()

    # URL input and button - centered by block-container styling
    url = st.text_input(
        "URLを入力してください",
        placeholder="https://example.com",
        key="url_input",
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Black button
    if st.button("要約を開始", use_container_width=True):
        if url.strip():
            # Show processing message
            with st.spinner("ページを分析中..."):
                try:
                    # Store URL in session state
                    st.session_state.target_url = url.strip()
                    
                    # Scrape the webpage
                    scraping_service = ScrapingService()
                    scraped_content = scraping_service.scrape(url.strip())
                    
                    # Generate summary using existing ollama client
                    if "ollama_client" in st.session_state:
                        summarization_service = SummarizationService(st.session_state.ollama_client)
                        summary = asyncio.run(summarization_service.summarize(scraped_content))
                        st.session_state.page_summary = summary
                    else:
                        st.session_state.page_summary = "要約を生成できませんでした。"
                    
                    # Reset messages for new session
                    if "messages" in st.session_state:
                        st.session_state.messages = []
                    
                    # Navigate to chat after processing
                    st.session_state.show_chat = True
                    st.rerun()
                    
                except ValueError as e:
                    st.error(f"エラー: {str(e)}")
                except SummarizationServiceError as e:
                    st.error(f"要約エラー: {str(e)}")
                except Exception as e:
                    st.error(f"予期しないエラーが発生しました: {str(e)}")
        else:
            st.error("URLを入力してください")
    
    # Footer component
    render_footer()