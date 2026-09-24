from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PATH = Path(__file__).parent / "chroma_db"

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path=str(CHROMA_PATH))

collection = client.get_or_create_collection(
    name="ecommerce_faq",
    embedding_function=embedding_function,
)


def search_faq(query: str, k: int = 3) -> str:
    results = collection.query(query_texts=[query], n_results=k)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    if not docs:
        return "No matching FAQ found."
    lines = []
    for doc, meta in zip(docs, metas):
        question = (meta or {}).get("question", "")
        lines.append(f"Q: {question}\nA: {doc}")
    return "\n\n".join(lines)
