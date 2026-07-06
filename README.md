# 🏦 Jeanie — AI Banking Assistant

An agentic AI banking assistant modeled after Fifth Third Bank's "Jeanie" chatbot. Built with LangGraph and LangChain, backed by a hosted LLM, combining structured data lookups, semantic policy search (RAG), and human-in-the-loop approval for sensitive actions — all in a live, publicly deployed app.

**🔗 Live demo:** https://jeanie-banking-agent.streamlit.app

## What it does

- Look up any of 250 synthetic customers by name or ID (balances, cards, account details)
- Run portfolio-wide analytics ("how many customers have checking balances over $5,000?")
- Generate full account statements and transaction-level analytics
- Answer bank policy questions (overdrafts, disputes, card replacement, account closure) using semantic search over real policy documents
- Require human approval before executing sensitive actions like transfers or reporting a lost card

## Architecture

## Tech stack

**Orchestration:** LangGraph, LangChain
**LLM:** Llama 3.3 70B via Groq (free-tier hosted inference)
**RAG:** sentence-transformers (embeddings) + FAISS (vector search)
**Data:** pandas + openpyxl over a synthetic 250-customer Excel dataset
**Frontend:** Streamlit, deployed on Streamlit Community Cloud
**Secrets management:** Streamlit Cloud encrypted Secrets (no keys committed to source)

## Key engineering decisions

- **Human-in-the-loop approval**: sensitive actions (transfers, card reports) pause execution via LangGraph's `interrupt()`/`Command(resume=...)` pattern until a human explicitly approves or denies.
- **RAG over hardcoded prompts**: policy documents are chunked, embedded, and retrieved via FAISS rather than stuffed into the prompt, keeping the system scalable to more documents.
- **Per-session conversation threads**: each browser session gets its own LangGraph memory thread, so conversations never leak between users.
- **Graceful degradation**: malformed or ambiguous questions return a friendly rephrase prompt instead of crashing the app.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

You'll need a free Groq API key (console.groq.com) in a local `.env` file:

## Possible extensions

- Swap the mock/Excel data for real core-banking API integrations
- Add authentication/authorization per bank employee
- Move from in-memory FAISS to a production vector database (pgvector, Pinecone)
- Add audit logging for every tool call and approval decision