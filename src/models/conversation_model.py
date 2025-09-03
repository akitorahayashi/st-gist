import re
from typing import Any, AsyncGenerator

from src.protocols.models.conversation_model_protocol import ConversationModelProtocol


class ConversationModel(ConversationModelProtocol):
    def __init__(self, client: Any):
        self.client = client
        self.messages = []
        self.is_responding = False
        self.last_error = None

    async def generate_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Generates a response from the client as an asynchronous stream.
        """
        self.is_responding = True
        self.last_error = None
        try:
            async for chunk in self.client.generate(user_message):
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
        return await self.client.generate_once(user_message)

    async def respond_to_user_message(self, user_message: str, summary: str = "", scraped_content: str = "") -> str:
        """
        Generate a response to user message with automatic state management using Web Page Q&A format.

        Args:
            user_message: The user's message to respond to
            summary: The summarization of the web page
            scraped_content: The scraped content from the web page

        Returns:
            str: The AI's response
        """
        self.is_responding = True
        try:
            # Build the Web Page Q&A prompt
            qa_prompt = f"""# AI Prompt

## Role

You are a "Web Page Q&A Bot".

## Context

You will be given the text content of a web page and a user's question. Your task is to answer the question based strictly on the provided text.

## Instructions

1. Analyze the user's question.

2. Carefully scan the provided "Web Page Text" to find the relevant information to answer the question.

3. Formulate a concise and accurate answer based *only* on the information found in the text.

## Constraints

- **DO NOT** use any external knowledge or information outside of the provided "Web Page Text".

- **MUST** respond in the same language as the user's question.

- If the answer cannot be found within the text, you **MUST** respond with: "I could not find the answer to your question in the provided text." (in the same language as the user's question)

- Do not invent, assume, or infer any information that is not explicitly stated in the text.

---

## [Input Placeholders]

### Your Summarization:

{summary}

### User Question:

{user_message}

### Web Page Text:

{scraped_content}"""

            response = await self.generate_response_once(qa_prompt)
            return response
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
