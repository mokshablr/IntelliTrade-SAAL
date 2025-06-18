import streamlit as st
import random
import time
import requests
import os

from dotenv import load_dotenv

load_dotenv()

llm_api_endpoint = os.getenv("LLM_API_ENDPOINT")

st.write("Welcome to IntelliTrade!")

st.caption("Use this chatbot to learn about trading and use it as your trading assistant.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        payload = {
                "user_input":prompt
                }

        try: 
            if llm_api_endpoint == None or llm_api_endpoint == "":
                data = { "message": "This chatbot is not connected to an LLM." }
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

        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
