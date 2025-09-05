# ConversationModel Requirements

## Stream Support
- ConversationModel must support both streaming and non-streaming responses
- `generate_response()`: Returns AsyncGenerator for streaming
- `generate_response_once()`: Returns complete response at once
- `respond_to_user_message()`: Uses non-streaming for UI compatibility

## UI Integration
- Chat responses in UI should be synchronous (non-streaming)
- Use `respond_to_user_message()` method for chat functionality
- Streaming methods available for other use cases if needed

## Core Methods
- Both streaming and non-streaming methods must be maintained
- Protocol interface defines both method signatures
- Implementation uses OllamaClientProtocol (gen_stream/gen_batch)