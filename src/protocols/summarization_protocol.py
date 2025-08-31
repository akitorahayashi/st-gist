from typing import Protocol


class SummarizationProtocol(Protocol):
    """
    Protocol for text summarization services.
    """
    
    async def summarize(self, text: str, max_chars: int = 10000) -> str:
        """
        Summarize the given text.

        Args:
            text: The text content to summarize.
            max_chars: The maximum number of characters to process.

        Returns:
            The summarized text.

        Raises:
            SummarizationServiceError: If summarization fails.
        """
        ...