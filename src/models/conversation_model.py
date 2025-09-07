import os
import re
from string import Template
from typing import AsyncGenerator

import streamlit as st
from sdk.olm_api_client import OllamaClientProtocol

from src.protocols.models.conversation_model_protocol import ConversationModelProtocol


class ConversationModel(ConversationModelProtocol):
    def __init__(self, client: OllamaClientProtocol):
        self.client = client
        self.messages = []
        self.is_responding = False
        self.last_error = None
        self._qa_prompt_template = self._load_qa_prompt_template()

    def _truncate_prompt(self, prompt: str, max_chars: int = None) -> str:
        """
        Truncate prompt from the end if it exceeds max_chars to preserve important context at the beginning.

        Args:
            prompt: The prompt to potentially truncate
            max_chars: Maximum number of characters allowed (default from MAX_PROMPT_LENGTH env var)

        Returns:
            str: Truncated prompt if necessary
        """
        if max_chars is None:
            max_chars = st.secrets.get("MAX_PROMPT_LENGTH", 4000)
        if len(prompt) <= max_chars:
            return prompt
        return prompt[:max_chars]

    def _load_qa_prompt_template(self) -> Template:
        """
        Load the Web Page Q&A prompt template from the static file.

        Returns:
            Template: The prompt template object

        Raises:
            FileNotFoundError: If the prompt template file is not found
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            "prompts",
            "web_page_qa_prompt.md",
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return Template(f.read())

    async def generate_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Generates a response from the client as an asynchronous stream.
        """
        self.is_responding = True
        self.last_error = None
        try:
            truncated_message = self._truncate_prompt(user_message)
            question_model = st.secrets.get("QUESTION_MODEL", "qwen3:0.6b")
            async for chunk in self.client.gen_stream(
                truncated_message, model=question_model
            ):
                yield chunk
        except Exception as e:
            self.last_error = str(e)
            raise
        finally:
            self.is_responding = False

    async def generate_response_once(self, user_message: str) -> str:
        """
        Generates a complete response from the client at once.
        """
        truncated_message = self._truncate_prompt(user_message)
        question_model = st.secrets.get("QUESTION_MODEL", "qwen3:0.6b")
        return await self.client.gen_batch(truncated_message, model=question_model)

    def _truncate_user_message(self, user_message: str, max_length: int = 1500) -> str:
        """
        ユーザーメッセージが長すぎる場合に末尾をカットし、メッセージを追加する。
        """
        suffix = "\n（質問が長すぎるためカットしました...）"
        if len(user_message) <= max_length:
            return user_message
        keep = max(0, max_length - len(suffix))
        return user_message[:keep] + suffix

    def _format_chat_history(self, max_length: int = 1500) -> str:
        """
        self.messagesをLLMプロンプト用の文字列にフォーマットする。
        古いメッセージから削除して、指定された最大長を超えないようにする。
        """
        if not self.messages:
            return ""

        history = []
        current_length = 0
        # 新しいメッセージから遡って履歴を構築 (最後のユーザーメッセージは除く)
        for msg in reversed(self.messages[:-1]):
            role = "ユーザー" if msg["role"] == "user" else "あなた"
            formatted_message = f'{role}: {msg["content"]}\n'

            # メッセージを追加すると最大長を超える場合はループを終了
            if current_length + len(formatted_message) > max_length:
                break

            history.insert(0, formatted_message)
            current_length += len(formatted_message)

        return "".join(history).strip()

    async def respond_to_user_message(
        self,
        user_message: str,
        summary: str = "",
        vector_search_content: str = "",
        page_content: str = "",
    ) -> str:
        """
        WebページのQ&A形式を使用して、自動状態管理でユーザーメッセージへの応答を生成します。
        """
        self.is_responding = True
        try:
            CONTEXT_MAX_LENGTH = int(st.secrets.get("CONTEXT_MAX_LENGTH", 1500))

            # ユーザーメッセージが長すぎる場合はカット
            truncated_user_message = self._truncate_user_message(
                user_message, max_length=CONTEXT_MAX_LENGTH
            )

            # 会話履歴の最大長を計算
            history_max_length = max(
                0, CONTEXT_MAX_LENGTH - len(truncated_user_message)
            )

            # 会話履歴をフォーマットする
            chat_history = self._format_chat_history(max_length=history_max_length)

            # WebページのQ&Aプロンプトを構築する
            qa_prompt = self._qa_prompt_template.safe_substitute(
                summary=summary,
                user_message=truncated_user_message,
                chat_history=chat_history,
                vector_search_content=vector_search_content,
                page_content=page_content,
            )

            # プロンプト全体の最終的な切り詰め（安全策）
            truncated_qa_prompt = self._truncate_prompt(qa_prompt)

            question_model = st.secrets.get("QUESTION_MODEL", "qwen3:0.6b")
            response = await self.client.gen_batch(
                truncated_qa_prompt, model=question_model
            )
            return response
        except Exception:
            self.last_error = "応答の生成に失敗しました。"
            raise
        finally:
            self.is_responding = False

    def add_user_message(self, content: str):
        """
        Add a user message to the chat history.
        """
        self.messages.append({"role": "user", "content": content})

    def add_ai_message(self, content: str):
        """
        Add an AI message to the chat history.
        """
        self.messages.append({"role": "ai", "content": content})

    def reset(self):
        """
        Reset the chat history.
        """
        self.messages = []
        self.is_responding = False
        self.last_error = None

    def should_respond(self) -> bool:
        """
        Check if AI should respond based on the internal message state.
        """
        return (
            len(self.messages) > 0
            and self.messages[-1]["role"] == "user"
            and not self.is_responding
        )

    def extract_think_content(self, text: str) -> tuple[str, str]:
        """
        Extract think content from text and return (thinking_content, remaining_text).

        Args:
            text: Input text that may contain <think> tags

        Returns:
            tuple of (thinking_content, text_without_think_tags)
        """
        # Pattern to match think tags and their content
        think_pattern = r"<think>(.*?)</think>"

        # Find all think content
        think_matches = re.findall(think_pattern, text, re.DOTALL)
        thinking_content = "\n".join(think_matches).strip()

        # Remove think tags from the original text
        cleaned_text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

        return thinking_content, cleaned_text

    def limit_messages(self, max_messages=10):
        """
        Limit the number of messages stored in the model.
        """
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
