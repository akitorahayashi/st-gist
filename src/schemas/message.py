from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MessageRole(str, Enum):
    """Message role enumeration for chat messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Chat message schema."""

    role: MessageRole
    content: Optional[str] = None
    think: Optional[str] = None  # Thinking process from olm-api v2
    response: Optional[str] = None  # Raw response from olm-api v2
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None
