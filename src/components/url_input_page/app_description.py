import streamlit as st


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
