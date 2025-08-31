import streamlit as st

from src.components.header import render_header

from .app_description import render_app_description
from .url_input import render_url_input_form


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    
    # Header component
    render_header()

    # Page container
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    
    # App description section
    st.markdown('<div class="description-section">', unsafe_allow_html=True)
    render_app_description()
    st.markdown('</div>', unsafe_allow_html=True)

    # URL input form section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    render_url_input_form()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Close page container
    st.markdown('</div>', unsafe_allow_html=True)

