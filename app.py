import uuid

import streamlit as st
from langgraph.types import Command
from agent import agent_graph
from customer_data_tools import CUSTOMERS_DF

st.set_page_config(
    page_title="Jeanie - Banking Assistant",
    page_icon="🏦",
    layout="wide",
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
.stChatMessage {
    border-radius: 14px;
    padding: 4px 8px;
}
.stat-card {
    background-color: #0B5ED7;
    color: white;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 14px;
}
.stat-card h3 { margin: 0 0 4px 0; font-size: 14px; opacity: 0.85; }
.stat-card p { margin: 0; font-size: 24px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

quick_prompt = None
with st.sidebar:
    st.markdown("### 🏦 Jeanie")
    st.caption("Bank employee assistant — look up any customer or bank policy.")

    total_customers = len(CUSTOMERS_DF)
    active_debit = (CUSTOMERS_DF["debit_card_status"] == "active").sum()
    active_credit = (CUSTOMERS_DF["credit_card_status"] == "active").sum()
    active_cards = int(active_debit + active_credit)
    total_cards_issued = int(
        CUSTOMERS_DF["debit_card_last4"].notna().sum()
        + CUSTOMERS_DF["credit_card_last4"].notna().sum()
    )

    st.markdown(f"""
    <div class="stat-card">
        <h3>Total Customers</h3>
        <p>{total_customers}</p>
    </div>
    <div class="stat-card">
        <h3>Active Cards</h3>
        <p>{active_cards}</p>
    </div>
    <div class="stat-card">
        <h3>Total Cards Issued</h3>
        <p>{total_cards_issued}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Example questions**")
    if st.button("🔍 Look up CUST0001", use_container_width=True):
        quick_prompt = "What are the account details for CUST0001?"
    if st.button("📄 Overdraft policy", use_container_width=True):
        quick_prompt = "What's the overdraft policy?"

st.title("🏦 Jeanie")
st.caption(
    "Ask about any customer's accounts, run portfolio analytics, or search bank policies.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
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
