import asyncio

import streamlit as st

from src.components.query_page.chat_section import render_chat_section
from src.models import ConversationModel



def render_query_page():
    st.empty()

    conversation_model: ConversationModel = st.session_state.get("conversation_model")

    summarization_model = st.session_state.get("summarization_model")
    scraping_model = st.session_state.get("scraping_model")
    try:
        with open("src/static/css/query_page.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    st.title("Query Page")

    target_url = st.session_state.get("target_url", "")
    scraped_content = scraping_model.content if scraping_model else ""
    if target_url:
        if len(target_url) > 50:
            truncated_url = target_url[:47] + "..."
            st.markdown(f"**対象URL**: [{truncated_url}]({target_url})")
        else:
            st.markdown(f"**対象URL**: [{target_url}]({target_url})")

    if scraped_content:
        with st.expander("取得したコンテンツ", expanded=False):
            st.write(scraped_content)

    if summarization_model and scraped_content:

        if not summarization_model.summary and not summarization_model.is_summarizing:

            try:
                with st.spinner("要約を開始しています..."):
                    # 思考過程用の固定expander
                    st.markdown("### 🤔 思考過程")
                    thinking_expander = st.expander("思考プロセス", expanded=True)
                    thinking_placeholder = thinking_expander.empty()

                    # 要約用プレースホルダー
                    summary_placeholder = st.empty()

                    async def stream_to_placeholders():
                        thinking_content = ""
                        summary_content = ""

                        try:
                            stream_generator = summarization_model.stream_summary(
                                scraped_content
                            )
                            async for thinking_chunk, summary_chunk in stream_generator:
                                thinking_content = thinking_chunk
                                summary_content = summary_chunk

                                # expanderの中身を更新
                                if thinking_content.strip():
                                    thinking_placeholder.markdown(thinking_content)

                                # 要約内容を表示
                                if summary_content.strip():
                                    summary_placeholder.markdown(summary_content)

                            # ストリーミング完了後はプレースホルダーをクリア（expanderは残す）
                            summary_placeholder.empty()

                        except Exception as e:
                            error_msg = f"要約の生成中にエラーが発生しました: {str(e)}"
                            summarization_model.last_error = str(e)
                            st.error(error_msg)

                            if (
                                "connection" in str(e).lower()
                                or "failed" in str(e).lower()
                            ):
                                st.info("💡 対処方法:")
                                st.code("ollama serve", language="bash")
                                st.markdown(
                                    "上記コマンドでOllamaサーバーを起動してから再試行してください。"
                                )
                            st.stop()

                    asyncio.run(stream_to_placeholders())
                if not summarization_model.last_error:
                    st.rerun()

            except Exception as outer_e:
                st.error(f"要約処理でエラーが発生しました: {str(outer_e)}")
                if "connection" in str(outer_e).lower():
                    st.info("💡 Ollamaサーバーが起動していることを確認してください")
                    st.code("ollama serve", language="bash")
                st.stop()
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

            if (
                "接続" in summarization_model.last_error
                or "connection" in summarization_model.last_error.lower()
            ):
                st.info("💡 対処方法:")
                st.code("ollama serve", language="bash")
                st.markdown(
                    "上記コマンドでOllamaサーバーを起動してから再試行してください。"
                )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("エラーをリセットして再試行"):
                    summarization_model.reset()
                    st.rerun()
            with col2:
                if st.button("DEBUG モードに切り替え"):
                    st.info("secrets.tomlで `DEBUG = true` に設定してください")
                    st.code("DEBUG = true", language="toml")
    if summarization_model and summarization_model.summary.strip():
        st.markdown("---")

    render_chat_section(conversation_model, scraping_model, summarization_model)
