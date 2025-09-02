import streamlit as st

from src.services.scraping_service import ScrapingService


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    app_state = st.session_state.app_state

    st.title("Gist")
    st.write(
        "By entering a URL, this tool will analyze and summarize the content of the page, allowing you to ask questions about it through a chatbot."
    )

    render_url_input_form()


def render_url_input_form():
    """Render URL input form with centered layout"""
    app_state = st.session_state.app_state

    # Load CSS for URL input page styling
    try:
        with open("src/static/css/url_input_page.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, continue without styling

    with st.container():
        url = st.text_input(
            "URLを入力してください",
            placeholder="https://example.com",
            key="url_input",
            label_visibility="collapsed",
            disabled=app_state.is_processing,
        )

        if app_state.last_error:
            st.error(app_state.last_error)
            app_state.clear_error()

        st.markdown("<br>", unsafe_allow_html=True)

        button_text = (
            "ページの内容を取得中..." if app_state.is_processing else "要約を開始"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            button_text, use_container_width=True, disabled=app_state.is_processing
        ):
            if url.strip():
                try:
                    ScrapingService().validate_url(url.strip())
                    app_state.start_summarization(url.strip())
                    scraped_content = ScrapingService().scrape(url.strip())
                    app_state.complete_summarization(scraped_content)
                    st.rerun()
                except ValueError as e:
                    app_state.set_error(f"{str(e)}")
                    st.rerun()
                except Exception as e:
                    app_state.set_error(f"エラーが発生しました: {str(e)}")
                    st.rerun()
            else:
                app_state.set_error("URLを入力してください")
                st.rerun()
