"""
Wraps the RAG pipeline (rag.py) as a tool the agent can call, so it can
answer policy/procedure questions grounded in real document text instead
of guessing.
"""
from langchain_core.tools import tool
from rag import build_knowledge_base, search

_index, _chunks = build_knowledge_base()


@tool
def search_policy_docs(query: str) -> str:
    """Search the bank's policy documents (overdraft, disputes, card
    replacement, account closure) to answer questions about bank policies,
    fees, timelines, and procedures.

    Args:
        query: The customer's question about a bank policy.
    """
    results = search(query, _index, _chunks, k=3)
    if not results:
        return "No relevant policy information found."
    return "\n\n".join(f"From {r['source']}:\n{r['text']}" for r in results)
