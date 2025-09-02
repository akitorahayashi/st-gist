import asyncio
from typing import AsyncGenerator

from src.protocols.models.conversation_model_protocol import ConversationModelProtocol


class MockConversationModel(ConversationModelProtocol):
    """
    Mock conversation model for testing and development.
    """

    def __init__(self, client=None):
        self.client = client  # Not used in mock but kept for compatibility
        self.messages = []
        self.is_responding = False

    async def generate_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Mock streaming response generation.
        """
        self.is_responding = True
        try:
            # Simulate streaming response
            mock_response = f"これは「{user_message}」に対するテスト用の応答です。"
            chunks = mock_response.split()
            
            for chunk in chunks:
                await asyncio.sleep(0.1)  # Simulate processing time
                yield chunk + " "
        finally:
            self.is_responding = False

    async def generate_response_once(self, user_message: str) -> str:
        """
        Mock complete response generation.
        """
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate different responses based on user input
        if "こんにちは" in user_message.lower() or "hello" in user_message.lower():
            return "こんにちは！何かお手伝いできることはありますか？"
        elif "質問" in user_message or "教えて" in user_message:
            return "ご質問ありがとうございます。テスト用のモックレスポンスです。"
        elif "要約" in user_message or "まとめ" in user_message:
            return "要約について説明いたします。これはテスト用の応答です。"
        else:
            return f"「{user_message}」についてお答えします。これはテスト環境での模擬応答です。"

    async def respond_to_user_message(self, user_message: str) -> str:
        """
        Generate a response to user message with automatic state management.
        """
        self.is_responding = True
        try:
            response = await self.generate_response_once(user_message)
            return response
        finally:
            self.is_responding = False

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the chat history.
        """
        self.messages.append({"role": "user", "content": content})

    def add_ai_message(self, content: str) -> None:
        """
        Add an AI message to the chat history.
        """
        self.messages.append({"role": "ai", "content": content})

    def reset(self) -> None:
        """
        Reset the chat history.
        """
        self.messages = []
        self.is_responding = False

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
        Mock implementation of think content extraction.
        """
        # Simple mock implementation - no actual think tags processing
        if "<think>" in text and "</think>" in text:
            start = text.find("<think>") + 7
            end = text.find("</think>")
            thinking_content = text[start:end].strip()
            cleaned_text = text.replace(f"<think>{thinking_content}</think>", "").strip()
            return thinking_content, cleaned_text
        return "", text

    def limit_messages(self, max_messages: int = 10) -> None:
        """
        Limit the number of messages in the conversation.
        """
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]