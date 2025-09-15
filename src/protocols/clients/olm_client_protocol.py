from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Protocol,
    Union,
    runtime_checkable,
)

from src.schemas import ChatResponse, ChatStreamResponse, Message


@runtime_checkable
class OlmClientV2Protocol(Protocol):
    """
    Protocol for Olm API v2 clients.

    Provides chat completion functionality with advanced features
    including conversation history, tool calling, and fine-grained generation control.
    """

    async def generate(
        self,
        messages: List[Message],
        model_name: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Union[ChatResponse, AsyncGenerator[ChatStreamResponse, None]]:
        """
        Generate chat completion using the v2 API.

        Args:
            messages: List of Message objects with role and content.
            model_name: The name of the model to use for generation.
            tools: Optional list of tool definitions for function calling.
            stream: Whether to stream the response.
            **kwargs: Additional generation parameters (temperature, top_p, etc.).

        Returns:
            ChatResponse (if stream=False) or AsyncGenerator[ChatStreamResponse] (if stream=True).
        """
        ...
