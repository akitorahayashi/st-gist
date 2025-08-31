import asyncio
from typing import AsyncGenerator

from src.clients.ollama_api_client.interface import OllamaClientInterface

# Streaming configuration
WORD_DELAY = 0.15  # Delay between words (seconds)


class MockOllamaApiClient(OllamaClientInterface):
    """
    A mock client for testing and development purposes.
    """

    def __init__(self):
        self.mock_responses = [
            "Hello! How can I help you today?",
            "That's an interesting question. Could you tell me more about it?",
            "I understand. Is there anything else you'd like to know?",
            "Yes, I think you're absolutely right about that.",
            "I'm sorry, but could you be more specific about what you're looking for?",
        ]
        self.response_index = 0

    async def _stream_response(self, response_text: str) -> AsyncGenerator[str, None]:
        """
        Stream a response text word by word (like real API).
        """
        words = response_text.split()
        for i, word in enumerate(words):
            await asyncio.sleep(WORD_DELAY)
            # Yield word with space (except for the last word)
            if i < len(words) - 1:
                yield word + " "
            else:
                yield word

    def generate(self, prompt: str, model: str = None) -> AsyncGenerator[str, None]:
        """
        Generates mock text responses with streaming.

        Args:
            prompt: The prompt to send to the model (ignored in mock).
            model: The name of the model to use for generation (ignored in mock).

        Returns:
            AsyncGenerator yielding text chunks.
        """
        # Custom responses for specific inputs
        custom_responses = {
            "hello": "Hello! Nice to meet you!",
            "hi": "Hi there! How are you doing?",
            "test": "This is a test response from the mock client.",
            "help": "I'm here to help! What would you like to know?",
            "thanks": "You're welcome! Happy to help anytime.",
        }

        # Check for custom responses
        for key, response in custom_responses.items():
            if prompt.lower().strip() == key.lower():
                return self._stream_response(response)

        # Default mock response
        response = self.mock_responses[self.response_index % len(self.mock_responses)]
        self.response_index += 1

        full_response = f"{response}\n\n(Mock response to: {prompt[:30]}{'...' if len(prompt) > 30 else ''})"

        return self._stream_response(full_response)
