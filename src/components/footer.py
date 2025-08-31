import streamlit as st


def render_footer():
    """Render the footer with author's GitHub link"""
    st.markdown(
        """
        <style>
        /* Global override for processing states */
        body, html, [data-testid="stApp"], .stApp, .main {
            background-color: inherit !important;
        }
        
        .footer {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100vw !important;
            background-color: #000000 !important;
            background: #000000 !important;
            padding: 1rem 2rem !important;
            text-align: center !important;
            border-top: 1px solid #333333 !important;
            font-size: 0.9rem !important;
            color: #ffffff !important;
            z-index: 999999 !important;
            box-sizing: border-box !important;
        }
        
        /* Multiple layers to ensure black background */
        .footer::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #000000 !important;
            background: #000000 !important;
            z-index: -1;
        }
        
        .footer::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #000000 !important;
            background: #000000 !important;
            z-index: -2;
        }
        
        /* Override any Streamlit processing overlays and states */
        [data-testid="stSpinner"] ~ .footer,
        .stSpinner ~ .footer,
        [data-testid="stStatusWidget"] ~ .footer,
        .footer,
        .footer * {
            background-color: #000000 !important;
            background: #000000 !important;
        }
        
        /* Force footer to stay on top during any processing */
        .main[data-testid="stMain"]::after {
            content: "";
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4rem;
            background-color: #000000 !important;
            z-index: 999998;
            pointer-events: none;
        }
        
        /* Ensure footer content stays above the overlay */
        .footer {
            z-index: 999999 !important;
            position: relative;
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
