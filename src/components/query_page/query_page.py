import asyncio

import streamlit as st

from src.components.query_page.chat_section import render_chat_section
from src.models import ConversationModel


def render_query_page():
    """Render query page with URL summary and chat functionality"""
    # Clear all previous page components immediately
    st.empty()

    conversation_model: ConversationModel = st.session_state.get("conversation_model")

    # Get models from session_state
    summarization_model = st.session_state.get("summarization_model")
    scraping_model = st.session_state.get("scraping_model")

    # Load CSS for query page styling
    try:
        with open("src/static/css/query_page.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS file not found, continue without styling

    st.title("Query Page")

    # Get all necessary data from models and session_state
    target_url = st.session_state.get("target_url", "")
    scraped_content = scraping_model.content if scraping_model else ""

    # Display target URL if available
    if target_url:
        # Truncate URL if longer than 50 characters but keep it clickable
        if len(target_url) > 50:
            truncated_url = target_url[:47] + "..."
            st.markdown(f"**対象URL**: [{truncated_url}]({target_url})")
        else:
            st.markdown(f"**対象URL**: [{target_url}]({target_url})")

    # Debug component: Display scraped content
    if scraped_content:
        with st.expander("取得したコンテンツ", expanded=False):
            st.write(scraped_content)

    # summarization_model と scraped_content が存在する場合に実行
    if summarization_model and scraped_content:

        # まだ要約が生成されておらず、現在要約中でもない場合
        if not summarization_model.summary and not summarization_model.is_summarizing:

            # 要約開始時にスピナーを表示
            try:
                with st.spinner("要約を開始しています..."):
                    # 新しいイベントループを作成
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # model から async
                    # generator を取得
                    stream_generator = summarization_model.stream_summary(
                        scraped_content
                    )

                    # プレースホルダーを作成
                    thinking_placeholder = st.empty()
                    summary_placeholder = st.empty()

                    # ストリームを処理し、プレースホルダーを更新する async 関数
                    async def stream_to_placeholders():
                        thinking_content = ""
                        summary_content = ""

                        try:
                            # stream_summary から (thinking, content) のタプルを受け取る
                            async for thinking_chunk, summary_chunk in stream_generator:
                                thinking_content = thinking_chunk
                                summary_content = summary_chunk

                                # プレースホルダーをリアルタイムで更新
                                thinking_placeholder.markdown(thinking_content + " ▌")
                                summary_placeholder.markdown(summary_content + " ▌")

                            # ストリーム終了後、カーソルなしで最終結果を表示
                            thinking_placeholder.markdown(thinking_content)
                            summary_placeholder.markdown(summary_content)

                            # 注: self.thinking, self.summary, self.is_summarizing の更新は
                            # summarization_model.py 側の finally ブロックで自動的に行われる

                        except Exception as e:
                            error_msg = f"要約の生成中にエラーが発生しました: {str(e)}"
                            summarization_model.last_error = str(e)

                            # スピナーを閉じてからエラーメッセージを表示して停止
                            st.error(error_msg)

                            # 接続エラーの場合は追加の情報を提供
                            if (
                                "connection" in str(e).lower()
                                or "failed" in str(e).lower()
                            ):
                                st.info("💡 対処方法:")
                                st.code("ollama serve", language="bash")
                                st.markdown(
                                    "上記コマンドでOllamaサーバーを起動してから再試行してください。"
                                )

                            st.stop()  # エラー時は描画を停止

                    # async 関数を実行
                    try:
                        loop.run_until_complete(stream_to_placeholders())
                    finally:
                        loop.close()

                # ストリームが完了した場合のみページを再描画する
                if not summarization_model.last_error:
                    st.rerun()

            except Exception as outer_e:
                # エラーハンドリング
                st.error(f"要約処理でエラーが発生しました: {str(outer_e)}")
                if "connection" in str(outer_e).lower():
                    st.info("💡 Ollamaサーバーが起動していることを確認してください")
                    st.code("ollama serve", language="bash")
                st.stop()

        # ストリーミングが完了した後（または既に完了していた場合）、
        # model に保存された最終結果を静的に表示する
        if summarization_model.thinking.strip():
            st.markdown("### 🤔 思考過程")
            with st.expander("思考プロセス", expanded=True):
                st.markdown(summarization_model.thinking)

        if summarization_model.summary.strip():
            st.markdown("### 📝 要約コンテンツ")
            st.markdown(summarization_model.summary)

        # エラーがある場合はエラーメッセージを表示
        elif summarization_model.last_error:
            st.error(f"要約生成エラー: {summarization_model.last_error}")

            # 接続エラーの場合は追加の情報を提供
            if (
                "接続" in summarization_model.last_error
                or "connection" in summarization_model.last_error.lower()
            ):
                st.info("💡 対処方法:")
                st.code("ollama serve", language="bash")
                st.markdown(
                    "上記コマンドでOllamaサーバーを起動してから再試行してください。"
                )

            # リセットボタンを提供
            col1, col2 = st.columns(2)
            with col1:
                if st.button("エラーをリセットして再試行"):
                    summarization_model.reset()
                    st.rerun()
            with col2:
                if st.button("DEBUG モードに切り替え"):
                    st.info("secrets.tomlで `DEBUG = true` に設定してください")
                    st.code("DEBUG = true", language="toml")

    # Add divider before chat if we have content
    if summarization_model and summarization_model.summary.strip():
        st.markdown("---")

    # Render chat section
    render_chat_section(conversation_model, scraping_model, summarization_model)
