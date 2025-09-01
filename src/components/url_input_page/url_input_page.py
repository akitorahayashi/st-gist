import streamlit as st

from src.services.scraping_service import ScrapingService

from .app_description import render_app_description
from .url_input import render_url_input_form


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    app_state = st.session_state.app_state

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
    if app_state.is_processing:
        try:
            # スクレイピング処理（ブロッキング）
            scraped_content = ScrapingService().scrape(app_state.target_url)
            app_state.complete_summarization(scraped_content)

            # ★★★ ページ遷移の直前にプレースホルダーを空にする ★★★
            placeholder.empty()
            st.rerun()

        except (ValueError, Exception) as e:
            # エラーが発生した場合は処理を中断し、エラーメッセージを表示
            app_state.set_error(f"エラーが発生しました: {str(e)}")
            # エラーが発生した場合もUIは再描画されるため、プレースホルダーはクリアしない
            st.rerun()
