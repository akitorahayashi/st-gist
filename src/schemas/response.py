from typing import List, Optional

from pydantic import BaseModel

from .message import Message, MessageRole


class Choice(BaseModel):
    """Choice object for chat completion response."""

    index: int
    message: Message
    finish_reason: Optional[str] = None


class StreamDelta(BaseModel):
    """Delta object for streaming responses - partial message content."""

    role: Optional[MessageRole] = None
    content: Optional[str] = None
    think: Optional[str] = None  # Thinking deltas from olm-api v2
    response: Optional[str] = None  # Response deltas from olm-api v2
    tool_calls: Optional[list] = None


class StreamChoice(BaseModel):
    """Choice object for streaming chat completion response."""

    index: int
    delta: StreamDelta
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Usage statistics for chat completion."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """Chat completion response schema."""

    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class ChatStreamResponse(BaseModel):
    """Streaming chat completion response schema."""

    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]
