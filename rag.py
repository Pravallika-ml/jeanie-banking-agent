"""
RAG pipeline: load policy documents, split them into chunks, embed them,
and store them in a vector database (FAISS) for retrieval.
"""
import os
import numpy as np
import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

POLICY_DIR = "policies"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def load_documents():
    docs = []
    for filename in os.listdir(POLICY_DIR):
        if filename.endswith(".txt"):
            path = os.path.join(POLICY_DIR, filename)
            with open(path, "r") as f:
                text = f.read()
            docs.append({"source": filename, "text": text})
    return docs


def chunk_documents(docs, chunk_size=400, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for doc in docs:
        pieces = splitter.split_text(doc["text"])
        for i, piece in enumerate(pieces):
            chunks.append({"source": doc["source"], "chunk_id": i, "text": piece})
    return chunks


def embed_chunks(chunks):
    texts = [c["text"] for c in chunks]
    vectors = embedding_model.encode(texts, show_progress_bar=False)
    return vectors


def build_vector_store(vectors):
    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(vectors).astype("float32"))
    return index


def search(query, index, chunks, k=3):
    query_vector = embedding_model.encode([query])
    _, indices = index.search(np.array(query_vector).astype("float32"), k)
    return [chunks[i] for i in indices[0]]


def build_knowledge_base():
    docs = load_documents()
    chunks = chunk_documents(docs)
    vectors = embed_chunks(chunks)
    index = build_vector_store(vectors)
    return index, chunks


if __name__ == "__main__":
    index, chunks = build_knowledge_base()
    print(f"Knowledge base ready: {len(chunks)} chunks indexed.\n")

    query = "My debit card got stolen, what should I do?"
    results = search(query, index, chunks, k=3)

    print(f"Query: {query}\n")
    for r in results:
        print(f"[{r['source']} chunk {r['chunk_id']}]")
        print(r["text"])
        print()
