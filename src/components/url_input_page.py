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
    """URL入力フォームを描画し、状態に基づいて処理を制御する"""
    app_router = st.session_state.app_router
    scraping_model = st.session_state.scraping_model

    # Load CSS for URL input page styling
    try:
        with open("src/static/css/url_input_page.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, continue without styling

    with st.container():
        # --- 処理中の場合のロジック ---
        if scraping_model.is_scraping:
            target_url = st.session_state.get("target_url", "")

            # 処理中のUI表示
            st.text_input(
                "URL", value=target_url, disabled=True, label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.button(
                "ページの内容を取得中...", use_container_width=True, disabled=True
            )

            # 実際のスクレイピング処理
            try:
                scraping_model.scrape(target_url)
                app_router.go_to_chat_page()
                st.rerun()
            except Exception:
                st.rerun()
            return

        # --- 待機中の場合のUI描画 ---
        st.text_input(
            "URLを入力してください",
            placeholder="https://example.com",
            key="url_input",
            label_visibility="collapsed",
        )

        if scraping_model.last_error:
            st.error(scraping_model.last_error)
            scraping_model.last_error = None

        st.markdown("<br>", unsafe_allow_html=True)

        def on_summarize_click():
            current_url = st.session_state.get("url_input", "")
            if not current_url.strip():
                scraping_model.last_error = "URLを入力してください"
                return
            try:
                scraping_model.validate_url(current_url.strip())
                app_router.set_target_url(current_url.strip())
                scraping_model.is_scraping = True
            except ValueError as e:
                scraping_model.last_error = str(e)

        st.button("要約を開始", use_container_width=True, on_click=on_summarize_click)
