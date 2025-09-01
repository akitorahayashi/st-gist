import streamlit as st

from src.components.header import render_header
from src.services.scraping_service import ScrapingService

from .app_description import render_app_description
from .url_input import render_url_input_form


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""

    # Header component
    render_header()

    # Page container
    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    placeholder = st.empty()
    is_processing = st.session_state.get("processing", False)

    if not is_processing:
        with placeholder.container():
            # App description section
            st.markdown('<div class="description-section">', unsafe_allow_html=True)
            render_app_description()
            st.markdown("</div>", unsafe_allow_html=True)

            # URL input form section
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            render_url_input_form()
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Processing logic is now handled here
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

    # Close page container
    st.markdown("</div>", unsafe_allow_html=True)