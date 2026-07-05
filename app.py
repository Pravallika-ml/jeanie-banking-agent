import streamlit as st
from langgraph.types import Command
from agent import agent_graph
from banking_tools import CUSTOMER

st.set_page_config(
    page_title="Jeanie - Banking Assistant",
    page_icon="🏦",
    layout="wide",
)

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.stChatMessage {
    border-radius: 14px;
    padding: 4px 8px;
}
.account-card {
    background-color: #0B5ED7;
    color: white;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 14px;
}
.account-card h3 { margin: 0 0 4px 0; font-size: 15px; opacity: 0.85; }
.account-card p { margin: 0; font-size: 26px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

quick_prompt = None
with st.sidebar:
    st.markdown("### 👤 " + CUSTOMER["name"])
    checking = CUSTOMER["accounts"]["checking"]["balance"]
    savings = CUSTOMER["accounts"]["savings"]["balance"]
    st.markdown(f"""
    <div class="account-card">
        <h3>Checking</h3>
        <p>${checking:,.2f}</p>
    </div>
    <div class="account-card">
        <h3>Savings</h3>
        <p>${savings:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Quick actions**")
    if st.button("💳 Check balance", use_container_width=True):
        quick_prompt = "What's my checking balance?"
    if st.button("🧾 Recent transactions", use_container_width=True):
        quick_prompt = "Show my recent checking transactions"
    if st.button("📄 Overdraft policy", use_container_width=True):
        quick_prompt = "What's the overdraft policy?"

st.title("🏦 Jeanie")
st.caption(
    "Your AI banking assistant — ask about balances, transactions, cards, or bank policies.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-session"
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None

config = {"configurable": {"thread_id": st.session_state.thread_id}}

for role, content in st.session_state.history:
    avatar = "🏦" if role == "assistant" else "🙂"
    with st.chat_message(role, avatar=avatar):
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
    if col1.button("✅ Approve"):
        run_graph(Command(resume=True))
        st.rerun()
    if col2.button("❌ Deny"):
        run_graph(Command(resume=False))
        st.rerun()
else:
    user_input = st.chat_input("Ask Jeanie about your accounts...")
    if quick_prompt:
        user_input = quick_prompt
    if user_input:
        st.session_state.history.append(("user", user_input))
        with st.spinner("Thinking..."):
            run_graph({"messages": [("user", user_input)]})
        st.rerun()
