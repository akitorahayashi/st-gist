import streamlit as st

from src.services.scraping_service import ScrapingService

from .app_description import render_app_description
from .url_input import render_url_input_form


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    app_state = st.session_state.app_state

    # st.containerを使用してセクションをグループ化
    with st.container():
        render_app_description()
        render_url_input_form()
