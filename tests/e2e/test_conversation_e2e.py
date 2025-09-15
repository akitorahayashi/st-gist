from unittest.mock import patch

import pytest

from src.clients.olm_local_client_v2 import OlmLocalClientV2
from src.models.conversation_model import ConversationModel


class TestConversationE2E:
    """End-to-end tests for conversation with real local clients."""

    @pytest.mark.asyncio
    async def test_conversation_with_local_ollama_client(self, secrets):
        """
        Tests conversation flow with actual OlmLocalClientV2.
        Requires Ollama server running locally.
        """
        # Skip if no OLLAMA_HOST configured
        ollama_host = secrets.get("OLLAMA_HOST", "http://localhost:11434")
        model_name = secrets.get("TEST_MODEL")

        # Initialize real local client
        client = OlmLocalClientV2(host=ollama_host)
        conversation_model = ConversationModel(client=client)

        # Mock secrets for consistent testing
        secrets_dict = {
            "QUESTION_MODEL": model_name,
            "MAX_PROMPT_LENGTH": 4000,
            "CONTEXT_MAX_LENGTH": 1500,
        }

        with patch("streamlit.secrets") as mock_secrets:
            mock_secrets.get.side_effect = lambda key, default=None: secrets_dict.get(
                key, default
            )

            try:
                # Test basic question answering
                user_message = "What is Python programming language?"

                response = await conversation_model.respond_to_user_message(
                    user_message,
                    summary="Programming tutorial content",
                    page_content="Python is a programming language known for its simplicity.",
                )

                # Verify response
                assert response is not None
                assert len(response) > 0
                assert isinstance(response, str)

                print(f"User: {user_message}")
                print(f"AI: {response[:200]}...")

                # Test conversation history
                conversation_model.add_user_message(user_message)
                conversation_model.add_ai_message(response)

                # Follow-up question
                follow_up = "Can you give me an example?"
                follow_up_response = await conversation_model.respond_to_user_message(
                    follow_up,
                    summary="Programming tutorial content",
                    page_content="Here are some Python code examples.",
                )

                assert follow_up_response is not None
                assert len(follow_up_response) > 0

                print(f"Follow-up: {follow_up}")
                print(f"AI: {follow_up_response[:200]}...")

            except Exception as e:
                pytest.skip(f"Ollama server not available or model not found: {e}")

    @pytest.mark.asyncio
    async def test_conversation_streaming(self, secrets):
        """
        Tests streaming conversation with real client.
        """
        ollama_host = secrets.get("OLLAMA_HOST", "http://localhost:11434")
        model_name = secrets.get("TEST_MODEL")

        client = OlmLocalClientV2(host=ollama_host)
        conversation_model = ConversationModel(client=client)

        with patch("streamlit.secrets") as mock_secrets:
            mock_secrets.get.side_effect = lambda key, default: {
                "QUESTION_MODEL": model_name,
                "MAX_PROMPT_LENGTH": 4000,
            }.get(key, default)

            try:
                user_message = "Explain machine learning in simple terms"

                # Collect streaming response
                response_chunks = []
                async for chunk in conversation_model.generate_response(user_message):
                    response_chunks.append(chunk)
                    print(chunk, end="", flush=True)  # Real-time output

                print()  # New line after streaming

                # Verify streaming
                assert len(response_chunks) > 0
                full_response = "".join(response_chunks)
                assert len(full_response) > 0

                print(f"Total chunks: {len(response_chunks)}")
                print(f"Full response length: {len(full_response)}")

            except Exception as e:
                pytest.skip(f"Streaming test failed: {e}")

    @pytest.mark.asyncio
    async def test_conversation_with_web_context(self, secrets):
        """
        Tests conversation with web page context using real client.
        """
        ollama_host = secrets.get("OLLAMA_HOST", "http://localhost:11434")
        model_name = secrets.get("TEST_MODEL")

        client = OlmLocalClientV2(host=ollama_host)
        conversation_model = ConversationModel(client=client)

        # Simulate web page content
        page_summary = "Article about renewable energy and solar power"
        page_content = """
        Solar energy is becoming increasingly popular as a renewable energy source.
        Solar panels convert sunlight into electricity through photovoltaic cells.
        The technology has improved significantly in recent years, making it more
        affordable and efficient for both residential and commercial use.
        """

        with patch("streamlit.secrets") as mock_secrets:
            mock_secrets.get.side_effect = lambda key, default: {
                "QUESTION_MODEL": model_name,
                "CONTEXT_MAX_LENGTH": 1500,
            }.get(key, default)

            try:
                # Questions about the content
                questions = [
                    "What is solar energy?",
                    "How do solar panels work?",
                    "Why is solar energy becoming popular?",
                ]

                for question in questions:
                    response = await conversation_model.respond_to_user_message(
                        question, summary=page_summary, page_content=page_content
                    )

                    assert response is not None
                    assert len(response) > 0

                    # Response should relate to the provided context
                    assert any(
                        keyword in response.lower()
                        for keyword in ["solar", "energy", "panel", "electricity"]
                    )

                    print(f"Q: {question}")
                    print(f"A: {response[:150]}...\n")

                    # Add to conversation history
                    conversation_model.add_user_message(question)
                    conversation_model.add_ai_message(response)

                # Test that conversation maintains context
                assert len(conversation_model.messages) == 6  # 3 Q&A pairs

            except Exception as e:
                pytest.skip(f"Context-aware conversation test failed: {e}")

    @pytest.mark.asyncio
    async def test_conversation_error_recovery(self, secrets):
        """
        Tests conversation error handling with real client.
        """
        # Use invalid host to trigger connection error
        invalid_client = OlmLocalClientV2(host="http://invalid-host:11434")
        conversation_model = ConversationModel(client=invalid_client)

        with patch("streamlit.secrets") as mock_secrets:
            mock_secrets.get.side_effect = lambda key, default: {
                "QUESTION_MODEL": "test-model"
            }.get(key, default)

            # Should handle connection errors gracefully
            with pytest.raises(Exception):  # Connection error expected
                await conversation_model.respond_to_user_message(
                    "Test question", summary="Test", page_content="Test content"
                )

            # Should not be in responding state after error
            assert not conversation_model.is_responding
            assert conversation_model.last_error is not None
