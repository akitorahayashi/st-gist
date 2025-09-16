import streamlit as st


def render_url_input_page():
    """Render complete URL input page with header, description, form, and footer"""
    # Removed unused variable 'app_router'

    st.title("💎 Gist")
    st.write(
        "URLを入力すると、そのページの内容を分析・要約し、チャットボットにページに関する質問ができるようになります。"
    )

    render_url_input_form()


def render_url_input_form():
    """URL入力フォームを描画し、状態に基づいて処理を制御する"""
    app_router = st.session_state.app_router
    scraping_model = st.session_state.scraping_model

    # Load CSS for URL input page styling
    css_files = [
        "src/static/css/base/root.css",
        "src/static/css/url_input_page.css",
        "src/static/css/base/custom-button.css",
    ]

    for css_file in css_files:
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            pass  # CSS file not found, continue without styling

    with st.container():
        # URL入力フィールド(処理中は無効化)
        target_url = st.session_state.get("target_url", "")
        url_value = (
            target_url
            if scraping_model.is_scraping
            else st.session_state.get("url_input", "")
        )

        st.text_input(
            "URLを入力してください" if not scraping_model.is_scraping else "URL",
            placeholder="https://example.com",
            value=url_value,
            key="url_input",
            disabled=scraping_model.is_scraping,
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
                # session_stateにフラグを設定して、メインループで処理させる
                st.session_state.should_start_scraping = True
                st.session_state.target_url_to_scrape = current_url.strip()
            except ValueError as e:
                scraping_model.last_error = str(e)

        # ボタンのテキストと状態を動的に設定
        button_text = (
            "ページの内容を取得中..." if scraping_model.is_scraping else "要約を開始"
        )
        button_disabled = scraping_model.is_scraping

        st.button(
            button_text,
            use_container_width=True,
            disabled=button_disabled,
            on_click=on_summarize_click if not scraping_model.is_scraping else None,
        )

        # 処理中の場合のスクレイピング処理
        if scraping_model.is_scraping:
            target_url = st.session_state.get("target_url", "")
            if not target_url:
                scraping_model.is_scraping = False
                scraping_model.last_error = "URLが未設定です。もう一度お試しください。"
                st.rerun()
                return
            try:
                scraping_model.scrape(target_url)

                app_router.go_to_chat_page()
                st.rerun()
            except Exception as e:
                scraping_model.is_scraping = False
                scraping_model.last_error = f"スクレイピングに失敗しました: {e}"
                st.rerun()

        if st.secrets.get("DEBUG"):
            st.info("現在Mockが使用されています。")

        # メインループでのフラグ処理
        if st.session_state.get("should_start_scraping", False):
            # フラグをクリアして、処理を開始
            st.session_state.should_start_scraping = False
            target_url = st.session_state.get("target_url_to_scrape", "")

            # 処理開始
            app_router.set_target_url(target_url)
            scraping_model.is_scraping = True
            st.rerun()  # メインループでのst.rerun()は有効
