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

    def _format_chat_history(self) -> str:
        """
        self.messagesをLLMプロンプト用の文字列にフォーマットする
        """
        if not self.messages:
            return ""

        # 最後のメッセージ（現在のユーザーの質問）は除く
        history_str = ""
        # 2つ前までのメッセージを履歴として含める
        for msg in self.messages[:-1]:
            role = "ユーザー" if msg["role"] == "user" else "AI"
            history_str += f'{role}: {msg["content"]}\n'
        return history_str.strip()

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
            # 会話履歴をフォーマットする
            chat_history = self._format_chat_history()

            # WebページのQ&Aプロンプトを構築する
            qa_prompt = self._qa_prompt_template.safe_substitute(
                summary=summary,
                user_message=user_message,
                chat_history=chat_history,  # chat_historyを追加
                vector_search_content=vector_search_content,
                page_content=page_content,
            )

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
