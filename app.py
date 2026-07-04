import streamlit as st
from langgraph.types import Command
from agent import agent_graph

st.set_page_config(page_title="Jeanie - Demo Banking Assistant", page_icon="🏦")
st.title("🏦 Jeanie (Demo)")
st.caption("A local, LangGraph-powered banking assistant with human-in-the-loop approval.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-session"
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None

config = {"configurable": {"thread_id": st.session_state.thread_id}}

for role, content in st.session_state.history:
    with st.chat_message(role):
        st.write(content)

def run_graph(input_data):
    result = agent_graph.invoke(input_data, config=config)
    if "__interrupt__" in result:
        st.session_state.pending_interrupt = result["__interrupt__"][0].value
    else:
        st.session_state.pending_interrupt = None
        reply = result["messages"][-1].content
        st.session_state.history.append(("assistant", reply))

if st.session_state.pending_interrupt:
    st.warning(st.session_state.pending_interrupt["message"])
    col1, col2 = st.columns(2)
    if col1.button("Approve"):
        run_graph(Command(resume=True))
        st.rerun()
    if col2.button("Deny"):
        run_graph(Command(resume=False))
        st.rerun()
else:
    user_input = st.chat_input("Ask Jeanie about your accounts...")
    if user_input:
        st.session_state.history.append(("user", user_input))
        with st.spinner("Thinking..."):
            run_graph({"messages": [("user", user_input)]})
        st.rerun()
