from abc import ABC, abstractmethod
from typing import AsyncGenerator


class OllamaClientInterface(ABC):
    """
    Abstract base class for Ollama API clients.
    """

    @abstractmethod
    def generate(self, prompt: str, model: str = None) -> AsyncGenerator[str, None]:
        """
        Generate text using the model with streaming.

        Args:
            prompt: The prompt to send to the model.
            model: The name of the model to use for generation.

        Returns:
            AsyncGenerator yielding text chunks.
        """
        pass
