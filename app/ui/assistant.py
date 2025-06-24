import streamlit as st
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()
llm_api_endpoint = os.getenv("LLM_API_ENDPOINT")

def render():
    st.header("Trading Learning Assistant")
    st.write("Use this chatbot to learn about trading and get assistance with your trading questions.")
    
    # Initialize chat history for learning tab
    if "learning_messages" not in st.session_state:
        st.session_state.learning_messages = [{"role": "assistant", "content": "Let's start learning about trading! 👇"}]
    
    # Initialize streaming state
    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = False
        st.session_state.full_response_text = "" # Store the full response from LLM
        st.session_state.current_display_length = 0 # How much of the full response to display
    
    # Create a container with fixed height to prevent layout shifts
    chat_container = st.container(height=500)
    
    with chat_container:
        # Display chat messages from history on app rerun
        for message in st.session_state.learning_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Show streaming message if currently streaming
        if st.session_state.is_streaming:
            with st.chat_message("assistant"):
                # Display a progressively longer substring of the full response
                display_content = st.session_state.full_response_text[:st.session_state.current_display_length]
                st.markdown(display_content + "▌") # Add the typing indicator
            
            # Increment the display length
            if st.session_state.current_display_length < len(st.session_state.full_response_text):
                # Adjust sleep time to control typing speed
                time.sleep(0.005) # Slower for better readability
                st.session_state.current_display_length += 1 # Reveal one character at a time
                st.rerun()
            else:
                # Streaming finished
                st.session_state.learning_messages.append({"role": "assistant", "content": st.session_state.full_response_text})
                st.session_state.is_streaming = False
                st.session_state.full_response_text = ""
                st.session_state.current_display_length = 0
                st.rerun()
    
    # Accept user input - this stays outside the container so it's always at bottom
    if prompt := st.chat_input("Ask me anything about trading..."):
        # Only process if not currently streaming
        if not st.session_state.is_streaming:
            # Add user message to chat history
            st.session_state.learning_messages.append({"role": "user", "content": prompt})
            
            # Get LLM response
            payload = {
                "user_input": prompt
            }
            try: 
                if llm_api_endpoint == None or llm_api_endpoint == "":
                    assistant_response = "This chatbot is not connected to an LLM."
                else:
                    response = requests.post(llm_api_endpoint, json=payload)
                    data = response.json()
                
                    if "message" in data:
                        assistant_response = data["message"]
                    elif "error" in data:
                        assistant_response = f"Error from LLM: {data['error']}"
                    else:
                        assistant_response = "Unexpected response format."
            except requests.exceptions.RequestException as e:
                assistant_response = f"❌ Failed to reach the server: {str(e)}"
            except ValueError:
                assistant_response = "❌ Received non-JSON response from LLM."
            
            # Start streaming
            st.session_state.is_streaming = True
            st.session_state.full_response_text = assistant_response
            st.session_state.current_display_length = 0
            st.rerun()
