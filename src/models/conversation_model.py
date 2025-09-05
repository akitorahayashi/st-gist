import os
import re
from string import Template

from sdk.olm_api_client import OllamaClientProtocol

from src.protocols.models.conversation_model_protocol import ConversationModelProtocol


class ConversationModel(ConversationModelProtocol):
    def __init__(self, client: OllamaClientProtocol):
        self.client = client
        self.messages = []
        self.is_responding = False
        self.last_error = None
        self._qa_prompt_template = self._load_qa_prompt_template()

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

    async def respond_to_user_message(
        self, user_message: str, summary: str = "", scraped_content: str = ""
    ) -> str:
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
            # Build the Web Page Q&A prompt using the loaded template
            qa_prompt = self._qa_prompt_template.safe_substitute(
                summary=summary,
                user_message=user_message,
                scraped_content=scraped_content,
            )

            response = await self.client.gen_batch(qa_prompt)
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
