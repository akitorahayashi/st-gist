import pytest


@pytest.mark.asyncio
async def test_conversation_flow(conversation_model, mock_secrets):
    """
    Tests the conversation flow with question and answer.
    """
    # Setup initial state
    assert len(conversation_model.messages) == 0
    assert not conversation_model.should_respond()

    # Add user message
    user_message = "What is Python?"
    conversation_model.add_user_message(user_message)

    assert len(conversation_model.messages) == 1
    assert conversation_model.messages[0]["role"] == "user"
    assert conversation_model.messages[0]["content"] == user_message
    assert conversation_model.should_respond()

    # Generate AI response
    ai_response = await conversation_model.respond_to_user_message(
        user_message, summary="Test summary", page_content="Test page content"
    )
    conversation_model.add_ai_message(ai_response.content or "")

    # Verify response
    assert ai_response is not None
    assert len(ai_response.content or "") > 0
    assert len(conversation_model.messages) == 2
    assert conversation_model.messages[1]["role"] == "assistant"
    assert conversation_model.messages[1]["content"] == (ai_response.content or "")
    assert not conversation_model.should_respond()  # Last message is AI


@pytest.mark.asyncio
async def test_conversation_with_history(conversation_model, mock_secrets):
    """
    Tests conversation with existing chat history.
    """
    # Build conversation history
    conversation_model.add_user_message("Hello")
    conversation_model.add_ai_message("Hi there!")
    conversation_model.add_user_message("How are you?")
    conversation_model.add_ai_message("I'm doing well, thank you!")

    # Add new user message
    new_message = "Can you help me with Python?"
    conversation_model.add_user_message(new_message)

    assert len(conversation_model.messages) == 5
    assert conversation_model.should_respond()

    # Generate response (should include history context)
    ai_response = await conversation_model.respond_to_user_message(
        new_message,
        summary="Python tutorial content",
        page_content="Python is a programming language...",
    )

    assert ai_response is not None
    assert len(ai_response.content or "") > 0


@pytest.mark.asyncio
async def test_conversation_streaming(conversation_model, mock_secrets):
    """
    Tests streaming response generation.
    """
    user_message = "Explain machine learning"

    # Collect streaming response
    response_parts = []
    async for chunk in conversation_model.generate_response(user_message):
        response_parts.append(chunk)

    # Verify streaming worked
    assert len(response_parts) > 0
    full_response = "".join(response_parts)
    assert len(full_response) > 0


@pytest.mark.asyncio
async def test_conversation_non_streaming(conversation_model, mock_secrets):
    """
    Tests non-streaming response generation.
    """
    user_message = "What is AI?"

    # Get complete response at once
    response = await conversation_model.generate_response_once(user_message)

    assert response is not None
    assert len(response) > 0


@pytest.mark.asyncio
async def test_conversation_message_limiting(conversation_model, mock_secrets):
    """
    Tests message history limiting functionality.
    """
    # Add many messages
    for i in range(15):
        conversation_model.add_user_message(f"Message {i}")
        conversation_model.add_ai_message(f"Response {i}")

    assert len(conversation_model.messages) == 30

    # Limit to 10 messages
    conversation_model.limit_messages(max_messages=10)

    assert len(conversation_model.messages) == 10
    # Should keep the most recent messages
    assert "Message 10" in conversation_model.messages[0]["content"]


@pytest.mark.asyncio
async def test_conversation_reset(conversation_model):
    """
    Tests conversation reset functionality.
    """
    # Build some conversation
    conversation_model.add_user_message("Hello")
    conversation_model.add_ai_message("Hi")
    conversation_model.is_responding = True
    conversation_model.last_error = "Some error"

    # Reset
    conversation_model.reset()

    assert len(conversation_model.messages) == 0
    assert not conversation_model.is_responding
    assert conversation_model.last_error is None
