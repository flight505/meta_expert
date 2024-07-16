#!/usr/bin/env python3
# To run this app, use the command: streamlit run app/streamlit_app.py

import logging
import os
import sys
from typing import Dict

import streamlit as st

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.meta_agent import (
    MetaExpert,
    NoToolExpert,
    Router,
    State,
    StateGraph,
    ToolExpert,
    set_chat_finished,
)
from utils.logging import setup_logging

# Setup logging
setup_logging(level=logging.DEBUG, log_file="streamlit_app.log")
logger = logging.getLogger(__name__)


def routing_function(state: State) -> str:
    decision = state["router_decision"]
    logger.debug(f"Routing function called. Decision: {decision}")
    return decision


st.set_page_config(page_title="Meta Expert Chat", layout="wide")


def initialize_workflow():
    graph = StateGraph()
    agent_kwargs = {
        "model": "claude-3-5-sonnet-20240620",
        "server": "claude",
        "temperature": 0.5,
    }
    tools_router_agent_kwargs = agent_kwargs.copy()
    tools_router_agent_kwargs["temperature"] = 0

    graph.add_node("meta_expert", MetaExpert(**agent_kwargs))
    graph.add_node("router", Router(**tools_router_agent_kwargs))
    graph.add_node("no_tool_expert", NoToolExpert(**agent_kwargs))
    graph.add_node("tool_expert", ToolExpert(**tools_router_agent_kwargs))
    graph.add_node("end_chat", set_chat_finished)

    graph.set_entry_point("meta_expert")
    graph.set_finish_point("end_chat")

    graph.add_edge("meta_expert", "router")
    graph.add_edge("tool_expert", "meta_expert")
    graph.add_edge("no_tool_expert", "meta_expert")
    graph.add_conditional_edge("router", routing_function)

    return graph


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_state" not in st.session_state:
    st.session_state.chat_state = State()
if "workflow" not in st.session_state:
    st.session_state.workflow = initialize_workflow()


def process_user_input(user_input: str):
    st.session_state.chat_state["user_input"] = user_input
    with st.spinner("Thinking..."):
        response = st.session_state.workflow.process(st.session_state.chat_state)
    st.session_state.messages.append({"role": "assistant", "content": response})


# Main layout
st.title("Meta Expert Chat")

# Sidebar
with st.sidebar:
    st.subheader("About")
    st.write("This is a Meta Expert Chat system powered by advanced AI agents.")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_state = State()
        st.session_state.workflow = initialize_workflow()
        st.experimental_rerun()

# Chat interface
chat_container = st.container()

# Input area
default_input = "write a blog on new streamlit Column configuration"
user_input = st.text_input("What would you like to know?", value=default_input)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    process_user_input(user_input)

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.container():
            st.write(f"{message['role'].capitalize()}: {message['content']}")

# Expandable sections for additional information
col1, col2 = st.columns(2)

with col1:
    with st.expander("Conversation History", expanded=False):
        st.json(st.session_state.chat_state.get("conversation_history", []))

with col2:
    with st.expander("Meta Prompt", expanded=False):
        st.json(st.session_state.chat_state.get("meta_prompt", []))
