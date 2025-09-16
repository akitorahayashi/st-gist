import os
from string import Template
from typing import AsyncGenerator

import streamlit as st

from src.protocols import ConversationModelProtocol, OlmClientV2Protocol
from src.schemas import Message, MessageRole


class ConversationModel(ConversationModelProtocol):
    def __init__(self, client: OlmClientV2Protocol):
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
            messages = [Message(role=MessageRole.USER, content=truncated_message)]
            stream = await self.client.generate(
                messages=messages, model_name=question_model, stream=True
            )
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
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
        messages = [Message(role=MessageRole.USER, content=truncated_message)]
        response = await self.client.generate(
            messages=messages, model_name=question_model, stream=False
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content or ""
        return ""

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
        page_content: str = "",
    ) -> Message:
        """
        WebページのQ&A形式を使用して、messages配列を活用した会話履歴でユーザーメッセージへの応答を生成します。
        """
        self.is_responding = True
        try:
            CONTEXT_MAX_LENGTH = int(st.secrets.get("CONTEXT_MAX_LENGTH", 1500))

            # ユーザーメッセージが長すぎる場合はカット
            truncated_user_message = self._truncate_user_message(
                user_message, max_length=CONTEXT_MAX_LENGTH
            )

            # WebページのQ&Aプロンプトを構築する（システムプロンプト）
            system_prompt = self._qa_prompt_template.safe_substitute(
                summary=summary,
                page_content=page_content,
            )

            # v2形式のmessages配列を構築
            messages = [Message(role=MessageRole.SYSTEM, content=system_prompt)]

            # 既存の会話履歴をmessages形式で追加（最新のユーザーメッセージ以外）
            for msg in self.messages[:-1]:
                role = (
                    MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
                )
                messages.append(Message(role=role, content=msg["content"]))

            # 現在のユーザーメッセージを追加
            messages.append(
                Message(role=MessageRole.USER, content=truncated_user_message)
            )

            question_model = st.secrets.get("QUESTION_MODEL", "qwen3:0.6b")
            response = await self.client.generate(
                messages=messages, model_name=question_model, stream=False
            )
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message
            # Return empty message if no response
            return Message(role=MessageRole.ASSISTANT, content="")
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

    def limit_messages(self, max_messages=10):
        """
        Limit the number of messages stored in the model.
        """
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
