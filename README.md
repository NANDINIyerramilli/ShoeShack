# ShoeShack - Enterprise Agentic RAG Ecommerce Chatbot

Enterprise-grade multi-agent RAG architecture for ecommerce customer support and product intelligence.

Built with:

* LangChain
* LangGraph (ReAct prebuilt)
* LangSmith
* GROQ (`openai/gpt-oss-120b`)
* MCP (FastMCP, SSE transport)
* ChromaDB + Sentence Transformers (`all-MiniLM-L6-v2`)
* SQLite
* FastAPI
* Streamlit
* UV workspace

---

# Architecture

```text
                          ┌────────────────────┐
                          │    User Client     │
                          │ (Streamlit / CLI)  │
                          └─────────┬──────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │      Main Orchestrator Agent   │
                   │  LangGraph ReAct + GROQ LLM    │
                   └──────────────┬─────────────────┘
                                  │
        ┌─────────────────┬───────┴───────┬──────────────────┐
        ▼                 ▼               ▼                  ▼
 ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
 │ MCP Server  │  │  SQL Agent   │  │ RAG (FAQ)   │  │  External    │
 │ Orders /    │  │  Product DB  │  │ ChromaDB    │  │  DuckDuckGo  │
 │ Complaints  │  │  NL → SQL    │  │ MiniLM-L6   │  │  Wikipedia   │
 │ SSE :8001   │  │  HTTP :8002  │  │ in-process  │  │  ArXiv       │
 └──────┬──────┘  └──────┬───────┘  └─────────────┘  └──────────────┘
        ▼                ▼
 SQLite (orders /   SQLite (products)
  tickets)
```

The Main Agent is a real LangGraph **ReAct** loop. The LLM decides which of the 7 tools to call:

| Tool             | Backend                                   |
| ---------------- | ----------------------------------------- |
| `search_faq`     | ChromaDB + `all-MiniLM-L6-v2`             |
| `web_search`     | DuckDuckGo                                |
| `wikipedia`      | Wikipedia API                             |
| `arxiv`          | ArXiv API                                 |
| `call_sql_agent` | HTTP POST → `sql_agent` (`:8002`)         |
| `get_orders`     | MCP `fetch_orders` (SSE `:8001`)          |
| `get_complaints` | MCP `fetch_complaints` (SSE `:8001`)      |

The SQL agent backs a Flipkart-style shoes catalog (~900 rows in
`sql_agent/db.sqlite`, table `product`) — see
[SQL Agent Pipeline](#sql-agent-pipeline) for the schema.

---

# Prerequisites

* Python 3.11+
* UV package manager
* A GROQ API key

```bash
# Install UV (macOS / Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

# Setup

## 1. Clone

```bash
git clone <repo-url>
cd ecomm_chatbot
```

## 2. Create `.env` at the project root

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=enterprise-rag
LANGCHAIN_TRACING_V2=true
```

## 3. Install dependencies

```bash
uv sync
```

## 4. Seed the databases

```bash
# MCP orders + tickets
cd mcp_server && uv run --package mcp_server python seed_data.py && cd ..

# Product catalog — loads sql_agent/products.csv into the `product` table
cd sql_agent && uv run --package sql_agent python seed_data.py && cd ..
```

## 5. Ingest the FAQ collection

```bash
cd rag && uv run --package rag python ingest.py && cd ..
```

This builds `rag/chroma_db/` using `all-MiniLM-L6-v2` (384-dim embeddings).

---

# Running the system

Open three terminals for the services, plus a fourth for the UI.

## Terminal 1 — MCP Server (port 8001, SSE)

```bash
cd mcp_server && uv run --package mcp_server python server.py
```

## Terminal 2 — SQL Agent (port 8002, HTTP)

```bash
cd sql_agent && uv run --package sql_agent python server.py
```

## Terminal 3 — Main Agent (CLI)

```bash
uv run --package main_agent python -m main_agent.agent
```

## Terminal 4 — Streamlit UI

```bash
uv run streamlit run main_agent/ui/app.py
```

> **Important:** the UI must be launched with `streamlit run`. Running
> `python main_agent/ui/app.py` directly will fail because Streamlit needs to
> bootstrap its own runtime.

The UI opens at `http://localhost:8501`.

---

# Example Queries

| Query                                     | Tool the agent should pick |
| ----------------------------------------- | -------------------------- |
| `What is your return policy?`             | `search_faq`               |
| `Show Nike running shoes under 5000`      | `call_sql_agent`           |
| `Show my orders`                          | `get_orders`               |
| `Any complaints on my account?`           | `get_complaints`           |
| `Latest AI recommendation system papers`  | `arxiv`                    |
| `Who invented the World Wide Web?`        | `wikipedia`                |
| `Current best Black Friday deals on TVs?` | `web_search`               |

---

# SQL Agent Pipeline

```text
input_guardrails → sql_generator (GROQ) → query_executor → output_guardrails → response_formatter
```

* Input guardrails block dangerous keywords (`DROP`, `DELETE`, `UPDATE`,
  `INSERT`, `ALTER`, `UNION`, SQL comments, multi-statement attacks).
* SQL is generated by the LLM with a schema-aware prompt
  ([sql_agent/prompts.py](sql_agent/prompts.py)).
* The generated SQL is re-validated (`SELECT`-only, single-statement).
* Output guardrails cap rows at 20 and strip noisy / PII-style fields
  (`email`, `phone`, `address`, `password`, `user_id`, `product_link`).
  `product_link` is dropped because Flipkart URLs are ~500 chars each — keeping
  them blows past Groq's 8k-tokens/min free-tier window on multi-row results.

## Catalog schema

The agent queries a single `product` table in
[sql_agent/db.sqlite](sql_agent/db.sqlite):

```sql
CREATE TABLE product (
    "index"        INTEGER,
    product_link   TEXT,
    title          TEXT,
    brand          TEXT,
    price          INTEGER,   -- INR
    discount       REAL,      -- fraction, e.g. 0.25 = 25% off
    avg_rating     REAL,      -- 0.0–5.0
    total_ratings  INTEGER
);
```

The seed data lives next to the script at [sql_agent/products.csv](sql_agent/products.csv)
(~900 rows, Flipkart shoes/sports footwear).

---

# MCP Tools

| Tool               | Description                |
| ------------------ | -------------------------- |
| `fetch_orders`     | Orders for a given user_id |
| `fetch_complaints` | Tickets for a given user_id|

Exposed by [mcp_server/server.py](mcp_server/server.py) over SSE.

---

# Project Layout

```text
ecomm_chatbot/
├── pyproject.toml          # UV workspace
├── .env                    # GROQ + LangSmith secrets
├── README.md
├── Technical_Design_Document.md
│
├── main_agent/             # ReAct orchestrator
│   ├── agent.py            # CLI entrypoint
│   ├── graph.py            # create_react_agent + GROQ
│   ├── tools.py            # 7 LangChain tools
│   ├── prompts.py
│   └── ui/app.py           # Streamlit UI
│
├── mcp_server/             # FastMCP, orders + tickets
├── sql_agent/              # FastAPI + LangGraph SQL pipeline
│   ├── server.py / agent.py / graph.py
│   ├── guardrails.py / prompts.py / database.py
│   ├── seed_data.py        # loads products.csv → db.sqlite
│   ├── products.csv        # seed source (Flipkart shoes catalog)
│   └── db.sqlite
├── rag/                    # ChromaDB FAQ retriever
└── tools/                  # External tool wrappers
```

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'main_agent'`

You ran the UI with plain `python`. Use `streamlit run` instead:

```bash
uv run streamlit run main_agent/ui/app.py
```

## ChromaDB dimension mismatch

If you swap embedding models, delete the persistent store and re-ingest:

```bash
rm -rf rag/chroma_db
cd rag && uv run --package rag python ingest.py
```

## Port already in use

```bash
lsof -i :8001   # or :8002 / :8501
kill -9 <PID>
```

---

# Observability

LangSmith tracing is enabled when `LANGCHAIN_TRACING_V2=true` and
`LANGSMITH_API_KEY` are present in `.env`.

---

# License

MIT
