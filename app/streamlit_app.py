import streamlit as st
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.meta_agent import MetaExpert, State, workflow

st.set_page_config(page_title="Meta Expert Chat", layout="wide")

st.title("Meta Expert Chat")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_state" not in st.session_state:
    st.session_state.chat_state = State()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Update chat state
    st.session_state.chat_state["user_input"] = prompt

    # Process the user input
    with st.spinner("Thinking..."):
        for event in workflow.stream(st.session_state.chat_state, {"recursion_limit": 30}):
            pass

    # Display assistant's response
    with st.chat_message("assistant"):
        response = st.session_state.chat_state["meta_prompt"][-1]["content"]
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar for additional information and controls
with st.sidebar:
    st.subheader("About")
    st.write("This is a Meta Expert Chat system powered by advanced AI agents.")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_state = State()
        st.experimental_rerun()

# Display conversation history and other relevant information
with st.expander("Conversation History", expanded=False):
    st.json(st.session_state.chat_state.get("conversation_history", []))

with st.expander("Meta Prompt", expanded=False):
    st.json(st.session_state.chat_state.get("meta_prompt", []))
