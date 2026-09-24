from pathlib import Path

import pandas as pd
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

RAG_DIR = Path(__file__).parent
CHROMA_PATH = RAG_DIR / "chroma_db"
FAQ_CSV = RAG_DIR / "faq.csv"

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path=str(CHROMA_PATH))

collection = client.get_or_create_collection(
    name="ecommerce_faq",
    embedding_function=embedding_function,
)

df = pd.read_csv(FAQ_CSV)

for idx, row in df.iterrows():
    collection.upsert(
        documents=[row["answer"]],
        metadatas=[{"question": row["question"]}],
        ids=[str(idx)],
    )

print(f"FAQ ingestion complete: {len(df)} entries -> {CHROMA_PATH}")
