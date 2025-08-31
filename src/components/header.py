import streamlit as st


def render_header():
    """Render the main header with Gist title"""
    st.markdown(
        """
        <style>
        /* Hide default Streamlit header */
        header[data-testid="stHeader"] {
            display: none;
        }
        
        /* Hide the toolbar */
        .stAppToolbar {
            display: none;
        }
        
        /* Custom header */
        .main-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: #000000;
            padding: 1rem 2rem;
            color: white;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 0;
        }
        
        /* Adjust main content padding */
        .main .block-container {
            padding-top: 5rem;
        }
        
        /* Hide the default top padding */
        .main > div:first-child {
            padding-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="main-header">
            <div class="header-title">Gist</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
