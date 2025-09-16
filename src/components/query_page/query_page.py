import asyncio
import html

import streamlit as st

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

    # --- 修正: 要約ロジック ---
    # summarization_model と scraped_content が存在する場合に実行
    if summarization_model and scraped_content:

        # まだ要約が生成されておらず、現在要約中でもない場合
        if not summarization_model.summary and not summarization_model.is_summarizing:

            # --- ここからが新しいストリーミング処理 ---

            # プレースホルダーを先に定義
            st.markdown("### 🤔 思考過程")
            thinking_expander = st.expander("思考プロセス", expanded=True)
            thinking_placeholder = thinking_expander.empty()

            st.markdown("### 📝 要約コンテンツ")
            summary_placeholder = st.empty()

            try:
                # 新しいイベントループを作成
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # model から async
                # generator を取得
                stream_generator = summarization_model.stream_summary(scraped_content)

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
                        st.error(f"要約の生成中にエラーが発生しました: {str(e)}")
                        summarization_model.last_error = str(e)
                        # モデル側でエラーが発生しても is_summarizing は False になる

                # async 関数を実行
                loop.run_until_complete(stream_to_placeholders())

            finally:
                loop.close()

            # ストリームが完了（または失敗）したら、
            # モデルに保存された最終状態でページを再描画する
            st.rerun()
            # --- ここまでが新しいストリーミング処理 ---

        # ストリーミングが完了した後（または既に完了していた場合）、
        # model に保存された最終結果を静的に表示する
        if summarization_model.thinking.strip():
            st.markdown("### 🤔 思考過程")
            with st.expander("思考プロセス", expanded=True):
                st.markdown(summarization_model.thinking)

        if summarization_model.summary.strip():
            st.markdown("### 📝 要約コンテンツ")
            st.markdown(summarization_model.summary)

    # Add divider before chat if we have content
    if summarization_model and summarization_model.summary.strip():
        st.markdown("---")

    # --- Chat Logic --- #
    _render_chat_messages(
        conversation_model.messages, is_thinking=conversation_model.is_responding
    )

    prompt = st.chat_input(
        "このWebページへの質問", disabled=conversation_model.is_responding
    )

    if prompt:
        conversation_model.add_user_message(prompt)
        st.rerun()

    # If the last message is from the user and we should respond
    if conversation_model.should_respond():
        conversation_model.is_responding = True
        st.rerun()

    # Handle AI response generation
    if conversation_model.is_responding:
        try:
            user_query = conversation_model.messages[-1]["content"]
            # Get page content from scraping model
            page_content = scraping_model.content if scraping_model else ""
            # Get summary from summarization model
            page_summary = summarization_model.summary if summarization_model else ""

            # Create new event loop for chat response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                ai_message_object = loop.run_until_complete(
                    conversation_model.respond_to_user_message(
                        user_query,
                        summary=page_summary,
                        page_content=page_content,
                    )
                )
            finally:
                loop.close()

            # Display thinking process if available
            if ai_message_object.think and ai_message_object.think.strip():
                st.markdown("### 🤔 AI思考過程")
                with st.expander("思考プロセス", expanded=True):
                    st.markdown(ai_message_object.think)

            # Add only the content part to chat history (think is handled separately)
            conversation_model.add_ai_message(ai_message_object.content or "")
        except Exception as e:
            error_message = f"エラーが発生しました: {e}"
            conversation_model.last_error = error_message
            conversation_model.add_ai_message(error_message)
        finally:
            conversation_model.is_responding = False
            st.rerun()


def _render_chat_messages(messages, is_thinking=False):
    """
    Render all chat messages with a single style block by building a single HTML string.
    Also renders the thinking bubble if is_thinking is True.
    """
    messages_html_list = []
    for msg in messages:
        if msg["role"] == "user":
            messages_html_list.append(
                f"""
    <div class="user-message">
        <div class="user-content">
            {html.escape(msg["content"]).replace(chr(10), '<br>')}
        </div>
    </div>
    """
            )
        else:
            messages_html_list.append(
                f"""
    <div class="ai-message">
        <div class="ai-content">
            {html.escape(msg["content"]).replace(chr(10), '<br>')}
        </div>
    </div>
    """
            )

    # is_thinkingがTrueの場合、思考中バブルをリストの末尾に追加
    if is_thinking:
        messages_html_list.append(
            """
    <div class="thinking-message">
        <div class="thinking-content">
            <div style="display: flex; align-items: center;">
                <div class="thinking-dots">
                    Thinking...
                </div>
            </div>
        </div>
    </div>
    """
        )

    messages_html_string = "".join(messages_html_list)

    full_html = f"""
    <div class="chat-container">
    {messages_html_string}
    </div>
    """

    st.markdown(full_html, unsafe_allow_html=True)
