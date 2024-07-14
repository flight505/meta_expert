import streamlit as st
import sys
import os
from typing import List, Dict

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.meta_agent import MetaExpert, State, StateGraph, Router, NoToolExpert, ToolExpert, set_chat_finished

def routing_function(state: State) -> str:
    decision = state["router_decision"]
    print(f"\n\n Routing function called. Decision: {decision}")
    return decision

st.set_page_config(page_title="Meta Expert Chat", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_state" not in st.session_state:
    st.session_state.chat_state = State()
if "workflow" not in st.session_state:
    st.session_state.workflow = None

def initialize_workflow():
    graph = StateGraph(State)
    agent_kwargs = {
        "model": "claude-3-5-sonnet-20240620",
        "server": "claude",
        "temperature": 0.5
    }
    tools_router_agent_kwargs = agent_kwargs.copy()
    tools_router_agent_kwargs["temperature"] = 0

    graph.add_node("meta_expert", lambda state: MetaExpert(**agent_kwargs).run(state=state))
    graph.add_node("router", lambda state: Router(**tools_router_agent_kwargs).run(state=state))
    graph.add_node("no_tool_expert", lambda state: NoToolExpert(**agent_kwargs).run(state=state))
    graph.add_node("tool_expert", lambda state: ToolExpert(**tools_router_agent_kwargs).run(state=state))
    graph.add_node("end_chat", lambda state: set_chat_finished(state))

    graph.set_entry_point("meta_expert")
    graph.set_finish_point("end_chat")

    graph.add_edge("meta_expert", "router")
    graph.add_edge("tool_expert", "meta_expert")
    graph.add_edge("no_tool_expert", "meta_expert")
    graph.add_conditional_edges(
        "router",
        lambda state: routing_function(state),
    )
    return graph.compile()

def process_user_input(user_input: str):
    st.session_state.chat_state["user_input"] = user_input
    with st.spinner("Thinking..."):
        for event in st.session_state.workflow.stream(st.session_state.chat_state, {"recursion_limit": 30}):
            pass
    response = st.session_state.chat_state["meta_prompt"][-1]["content"]
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
user_input = st.chat_input("What would you like to know?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    process_user_input(user_input)

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Expandable sections for additional information
col1, col2 = st.columns(2)

with col1:
    with st.expander("Conversation History", expanded=False):
        st.json(st.session_state.chat_state.get("conversation_history", []))

with col2:
    with st.expander("Meta Prompt", expanded=False):
        st.json(st.session_state.chat_state.get("meta_prompt", []))

# Initialize workflow if not already done
if st.session_state.workflow is None:
    st.session_state.workflow = initialize_workflow()
