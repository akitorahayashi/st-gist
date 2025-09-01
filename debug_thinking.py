#!/usr/bin/env python3

import asyncio
import streamlit as st

# Add src to path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dev.mocks.mock_ollama_client import MockOllamaApiClient
from src.components.think_display import update_thinking_content, render_think_display, clear_thinking_content

st.title("Debug Thinking Display")

if "debug_started" not in st.session_state:
    st.session_state.debug_started = False

if st.button("Start Debug Test"):
    st.session_state.debug_started = True
    clear_thinking_content()

if st.session_state.debug_started:
    st.write("## Debug Test Running")
    
    # Manual test
    if st.button("Test Manual Update"):
        result1 = update_thinking_content("<think>")
        st.write(f"After '<think>': {result1}")
        
        result2 = update_thinking_content("Test content")
        st.write(f"After 'Test content': {result2}")
        
        result3 = update_thinking_content("</think>")
        st.write(f"After '</think>': {result3}")
        
        st.write(f"Session state: {dict(st.session_state)}")
    
    # Display current thinking
    st.write("## Current Thinking Display:")
    render_think_display(True)
    
    # Test with mock client
    if st.button("Test with Mock Client"):
        async def test_mock():
            client = MockOllamaApiClient()
            chunks = []
            
            async for chunk in client.generate("test prompt"):
                chunks.append(chunk)
                thinking_complete = update_thinking_content(chunk)
                
                if thinking_complete:
                    st.write(f"Thinking completed after {len(chunks)} chunks")
                    break
                    
                if len(chunks) > 50:  # Safety limit
                    st.write("Reached chunk limit")
                    break
                    
            st.write(f"Total chunks: {len(chunks)}")
            st.write(f"Final thinking: {st.session_state.get('current_thinking', '')}")
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(test_mock())
