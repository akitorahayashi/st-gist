import streamlit as st


def render_footer():
    """Render the footer with author's GitHub link"""
    st.markdown(
        """
        <style>
        .footer {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            background-color: #000000 !important;
            padding: 1rem 2rem !important;
            text-align: center !important;
            border-top: 1px solid #333333 !important;
            font-size: 0.9rem !important;
            color: #ffffff !important;
            z-index: 999 !important;
        }
        .footer a {
            color: #007bff !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        .footer a:hover {
            color: #0056b3 !important;
            text-decoration: underline !important;
        }
        /* Add bottom padding to main content to account for fixed footer */
        .main .block-container {
            padding-bottom: 4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="footer">
            Created by <a href="https://github.com/akitorahayashi" target="_blank" rel="noopener noreferrer">akitorahayashi</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
