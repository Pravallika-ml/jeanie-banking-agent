"""
The agent 'brain': combines banking action tools, policy-document RAG, and
customer-data lookup/analytics tools into one LangGraph agent. Uses Groq's
hosted Llama model instead of local Ollama so it works once deployed.
"""
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from banking_tools import ALL_TOOLS as BANKING_TOOLS
from policy_tools import search_policy_docs
from customer_data_tools import CUSTOMER_DATA_TOOLS

ALL_TOOLS = BANKING_TOOLS + [search_policy_docs] + CUSTOMER_DATA_TOOLS

SYSTEM_PROMPT = """You are Jeanie, a friendly banking assistant for a demo bank.
For the single demo customer (Alex Morgan), you can check balances, show
transactions, transfer money, activate/report cards, and file disputes.
You can answer bank policy questions by searching policy documents with
search_policy_docs. You can look up any of the bank's 250 customers with
get_customer_details, passing EITHER a name or a customer ID directly --
it accepts both. You can answer analytics questions across all 250 using
count_customers, average_balance, and list_customers.
Always use the right tool instead of guessing. When a tool returns a
specific number (a count, an average, a balance), always repeat that exact
number back to the customer in your reply -- never respond vaguely.
Be concise and warm."""

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


def call_model(state: MessagesState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(ALL_TOOLS)

builder = StateGraph(MessagesState)
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

checkpointer = MemorySaver()
agent_graph = builder.compile(checkpointer=checkpointer)
