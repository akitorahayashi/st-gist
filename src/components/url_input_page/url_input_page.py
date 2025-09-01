import streamlit as st

from src.components.header import render_header
from src.services.scraping_service import ScrapingService

from .app_description import render_app_description
from .url_input import render_url_input_form


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""

    render_header()

    # UI要素全体を保持するプレースホルダーを作成
    placeholder = st.empty()

    # プレースホルダー内にUIを描画
    with placeholder.container():
        st.markdown('<div class="page-container">', unsafe_allow_html=True)
        st.markdown('<div class="description-section">', unsafe_allow_html=True)
        render_app_description()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        render_url_input_form()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # UIを描画した後に、処理状態を確認してスクレイピングを実行
    if st.session_state.get("processing", False):
        try:
            # スクレイピング処理（ブロッキング）
            scraped_content = ScrapingService().scrape(st.session_state.target_url)
            st.session_state.scraped_content = scraped_content

            # 処理状態をクリーンアップ
            st.session_state.processing = False
            st.session_state.pop("target_url", None)

            if "messages" in st.session_state:
                st.session_state.messages = []

            # ★★★ ページ遷移の直前にプレースホルダーを空にする ★★★
            placeholder.empty()

            # 要約・チャットページへ遷移
            st.session_state.show_chat = True
            st.rerun()

        except (ValueError, Exception) as e:
            # エラーが発生した場合は処理を中断し、エラーメッセージを表示
            st.session_state.processing = False
            st.session_state.last_error = f"エラーが発生しました: {str(e)}"
            # エラーが発生した場合もUIは再描画されるため、プレースホルダーはクリアしない
            st.rerun()