import asyncio
import time

import streamlit as st


class ConversationService:
    def __init__(self, client):
        self.client = client

    def handle_ai_thinking(self):
        """
        Handle AI thinking state with streaming.
        """
        if st.session_state.get("ai_thinking", False):
            if not st.session_state.get("streaming_active", False):
                # Initialize streaming
                self._start_streaming()
            elif st.session_state.get("streaming_active", False):
                # Continue streaming
                self._continue_streaming()

    def _start_streaming(self):
        """
        Start streaming response.
        """
        try:
            user_message = st.session_state.messages[-1]["content"]

            # Initialize streaming state
            st.session_state.streaming_active = True
            st.session_state.streaming_response = ""
            st.session_state.streaming_complete = False

            # Add empty AI message placeholder
            st.session_state.messages.append({"role": "ai", "content": ""})

            # Get streaming chunks
            self._prepare_streaming_chunks(user_message)

        except Exception as e:
            st.error(f"Streaming initialization error: {str(e)}")
            self._cleanup_streaming()

    def _prepare_streaming_chunks(self, user_message):
        """
        Prepare streaming chunks from client.
        """
        try:

            async def get_chunks():
                chunks = []
                async for chunk in self.client.generate(user_message):
                    chunks.append(chunk)
                return chunks

            # Use a local event loop with a try/finally to ensure it's closed
            loop = asyncio.new_event_loop()
            try:
                st.session_state.stream_chunks = loop.run_until_complete(get_chunks())
                st.session_state.chunk_index = 0
            finally:
                loop.close()

            # Start streaming
            self._continue_streaming()

        except Exception as e:
            st.error(f"Chunk preparation error: {str(e)}")
            self._cleanup_streaming()

    def _continue_streaming(self):
        """
        Continue streaming next chunk.
        """
        try:
            if (
                "stream_chunks" in st.session_state
                and "chunk_index" in st.session_state
            ):

                chunks = st.session_state.stream_chunks
                index = st.session_state.chunk_index

                if index < len(chunks):
                    # Add next chunk
                    st.session_state.streaming_response += chunks[index]
                    st.session_state.chunk_index += 1

                    # Update AI message
                    if (
                        st.session_state.messages
                        and st.session_state.messages[-1]["role"] == "ai"
                    ):
                        st.session_state.messages[-1][
                            "content"
                        ] = st.session_state.streaming_response

                    # Schedule next update
                    time.sleep(0.05)  # Small delay for visual streaming effect
                    st.rerun()

                else:
                    # Streaming complete
                    self._finish_streaming()
        except Exception as e:
            st.error(f"Streaming error: {str(e)}")
            self._cleanup_streaming()

    def _finish_streaming(self):
        """
        Finish streaming and cleanup.
        """
        st.session_state.streaming_complete = True
        self._cleanup_streaming()
        self.limit_messages()
        st.rerun()

    def _cleanup_streaming(self):
        """
        Clean up streaming state.
        """
        st.session_state.ai_thinking = False
        st.session_state.streaming_active = False

        # Clean up streaming variables
        for key in [
            "stream_chunks",
            "chunk_index",
            "streaming_response",
            "streaming_complete",
        ]:
            if key in st.session_state:
                del st.session_state[key]

    def should_start_ai_thinking(self):
        """
        Check if AI thinking should be started.
        """
        return (
            len(st.session_state.messages) > 0
            and st.session_state.messages[-1]["role"] == "user"
            and not st.session_state.get("ai_thinking", False)
        )

    def limit_messages(self, max_messages=10):
        """
        Limit the number of messages in session state.
        """
        if len(st.session_state.messages) > max_messages:
            st.session_state.messages = st.session_state.messages[-max_messages:]
