from typing import AsyncGenerator, Protocol


class ConversationModelProtocol(Protocol):
    """
    Protocol for conversation models.
    """

    async def generate_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Generates a response from the client as an asynchronous stream.

        Args:
            user_message: The user's message to respond to

        Returns:
            AsyncGenerator[str, None]: Stream of response chunks
        """
        ...

    async def generate_response_once(self, user_message: str) -> str:
        """
        Generates a complete response from the client at once.

        Args:
            user_message: The user's message to respond to

        Returns:
            str: The complete response
        """
        ...

    async def respond_to_user_message(self, user_message: str) -> str:
        """
        Generate a response to user message with automatic state management.

        Args:
            user_message: The user's message to respond to

        Returns:
            str: The AI's response
        """
        ...

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the chat history.

        Args:
            content: The user's message content
        """
        ...

    def add_ai_message(self, content: str) -> None:
        """
        Add an AI message to the chat history.

        Args:
            content: The AI's message content
        """
        ...

    def reset(self) -> None:
        """
        Reset the chat history.
        """
        ...

    def should_respond(self) -> bool:
        """
        Check if AI should respond based on the internal message state.

        Returns:
            bool: True if AI should respond
        """
        ...

    def extract_think_content(self, text: str) -> tuple[str, str]:
        """
        Extract think content from text and return (thinking_content, remaining_text).

        Args:
            text: Input text that may contain <think> tags

        Returns:
            tuple of (thinking_content, text_without_think_tags)
        """
        ...

    def limit_messages(self, max_messages: int = 10) -> None:
        """
        Limit the number of messages in session state.

        Args:
            max_messages: Maximum number of messages to keep
        """
        ...
