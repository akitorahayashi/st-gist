import streamlit as st


def render_footer():
    """Render the footer with author's GitHub link"""
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #000000;
            padding: 1rem 2rem;
            text-align: center;
            border-top: 1px solid #333333;
            font-size: 0.9rem;
            color: #ffffff;
            z-index: 999;
        }
        .footer a {
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }
        .footer a:hover {
            color: #0056b3;
            text-decoration: underline;
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