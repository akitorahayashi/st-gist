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

    # 処理状態を確認してスクレイピングを実行
    if app_state.is_processing:
        try:
            scraped_content = ScrapingService().scrape(app_state.target_url)
            app_state.complete_summarization(scraped_content)
            # ページ遷移のために再実行
            st.rerun()

        except (ValueError, Exception) as e:
            app_state.set_error(f"エラーが発生しました: {str(e)}")
            st.rerun()
        finally:
            app_state.complete_ai_response()
