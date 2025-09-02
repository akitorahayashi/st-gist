import streamlit as st


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    # Removed unused variable 'app_router'

    st.title("Gist")
    st.write(
        "By entering a URL, this tool will analyze and summarize the content of the page, allowing you to ask questions about it through a chatbot."
    )

    render_url_input_form()


def render_url_input_form():
    """Render URL input form with centered layout"""
    app_router = st.session_state.app_router
    scraping_model = st.session_state.get("scraping_model")

    # Load CSS for URL input page styling
    try:
        with open("src/static/css/url_input_page.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, continue without styling

    with st.container():
        is_scraping = scraping_model.is_scraping if scraping_model else False

        url = st.text_input(
            "URLを入力してください",
            placeholder="https://example.com",
            key="url_input",
            label_visibility="collapsed",
            disabled=is_scraping,
        )

        if app_router.last_error:
            st.error(app_router.last_error)
            app_router.clear_error()

        st.markdown("<br>", unsafe_allow_html=True)

        button_text = "ページの内容を取得中..." if is_scraping else "要約を開始"

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(button_text, use_container_width=True, disabled=is_scraping):
            if url.strip():
                try:
                    # Get scraping model from session_state
                    scraping_model = st.session_state.scraping_model

                    scraping_model.validate_url(url.strip())

                    # Store URL
                    st.session_state.target_url = url.strip()

                    # Scraping result is now stored in scraping_model.content automatically
                    scraping_model.scrape(url.strip())

                    app_router.go_to_chat_page()
                    st.rerun()
                except ValueError as e:
                    app_router.set_error(f"{str(e)}")
                    st.rerun()
                except Exception as e:
                    app_router.set_error(f"エラーが発生しました: {str(e)}")
                    st.rerun()
            else:
                app_router.set_error("URLを入力してください")
                st.rerun()
