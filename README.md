# ShoeShack - Enterprise Agentic RAG Ecommerce Chatbot

Enterprise-grade multi-agent RAG architecture for ecommerce customer support and product intelligence.

Built with:

LangGraph
LangChain
Groq Cloud API
FastMCP
ChromaDB
Sentence-Transformers
SQLite
FastAPI & Uvicorn
React 18 & Vite
Streamlit
External Tool APIs
Astral UV & npm

---

# Architecture
<img width="825" height="552" alt="image" src="https://github.com/user-attachments/assets/48d01e4a-a844-49b8-b4a7-168f25ddc64b" />
<img width="1916" height="856" alt="Screenshot 2026-09-24 222515" src="https://github.com/user-attachments/assets/08f77cc1-8989-4959-a278-7af6dc5dcab7" />
<img width="763" height="681" alt="Screenshot 2026-09-24 222655" src="https://github.com/user-attachments/assets/80ca0d56-59eb-4bc4-82ef-4c0e4db54d2c" />
<img width="1828" height="861" alt="Screenshot 2026-09-24 222721" src="https://github.com/user-attachments/assets/a4f1c860-b499-464f-bb62-5b095bdfec52" />



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

| Query                                                      | Tool the agent should pick |
| ---------------------------------------------------------- | -------------------------- |
| `"Show me running shoes under ₹1500"`                      | `call_sql_agent`           |
| `Find top-rated Nike shoes with more than 30% discount`    | `call_sql_agent`           |
| `Show my orders`                                           | `get_orders`               |
| `Any complaints on my account?`                            | `get_complaints`           |
| `What is your return policy for damaged items?`            | `search_faq`               |
| `Current best Black Friday deals on TVs?`                  | `web_search`               |

---

# SQL Agent Pipeline

```text
input_guardrails → sql_generator (GROQ) → query_executor → output_guardrails → response_formatter
```

User Query: "Find Campus running shoes under 1500"
                      │
                      ▼
       ┌──────────────────────────────┐
       │   1. input_guardrails        │  ◄── Blocks SQL injection & DDL/DML keywords
       └──────────────┬───────────────┘
                      ▼
       ┌──────────────────────────────┐
       │   2. sql_generator (Groq)    │  ◄── Generates SQL using schema-aware prompt
       └──────────────┬───────────────┘
                      ▼
       ┌──────────────────────────────┐
       │   3. query_executor          │  ◄── Re-validates SELECT-only & executes in SQLite
       └──────────────┬───────────────┘
                      ▼
       ┌──────────────────────────────┐
       │   4. output_guardrails       │  ◄── Caps at 5 rows & redacts sensitive fields
       └──────────────┬───────────────┘
                      ▼
       ┌──────────────────────────────┐
       │   5. response_formatter      │  ◄── Returns clean records to the orchestrator
       └──────────────┬───────────────┘
                      ▼
             Final Result / Table


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
Enterprise-Agentic-RAG-Ecomm-Chatbot-main/
│
├──  frontend/                     # Modern React 18 + Vite User Interface
│   ├──  dist/                     # Production build bundle (served by FastAPI at :8000)
│   ├──  public/                   # Static assets
│   │   └── background.jpg           # Hero sneaker backdrop image
│   ├──  src/
│   │   ├── App.jsx                  # Main chat interface, link previews & markdown rendering
│   │   ├── index.css                # Glassmorphic dark editorial UI styling
│   │   └── main.jsx                 # React root mount
│   ├── index.html                   # HTML template with Google Fonts (Inter & Plus Jakarta Sans)
│   ├── package.json                 # Node dependencies (lucide-react, react-markdown, remark-gfm)
│   └── vite.config.js               # Dev server configuration with API proxy to port 8000
│
├──  main_agent/                   # Central ReAct Orchestrator & API Server
│   ├── agent.py                     # Interactive CLI loop for terminal chatting
│   ├── api.py                       # FastAPI application (:8000); serves API + React build
│   ├── graph.py                     # LangGraph ReAct loop with singleton agent caching
│   ├── prompts.py                   # Main system prompt & tool selection rules
│   ├── tools.py                     # 7 LangChain tool definitions + FastMCP SSE client
│   └──  ui/
│       └── app.py                   # Alternative Streamlit chat interface (:8501)
│
├──  mcp_server/                   # Model Context Protocol (FastMCP) Service
│   ├── database.py                  # SQLite query handlers for orders and tickets
│   ├── models.py                    # Pydantic schemas (Order, Ticket)
│   ├── orders_complaints.db         # SQLite database storing customer orders and tickets
│   ├── seed_data.py                 # Mock database generator using Faker
│   └── server.py                    # FastMCP SSE service running on port 8001
│
├──  sql_agent/                    # Natural Language to SQL Product Catalog Agent
│   ├── agent.py                     # Execution wrapper for the SQL pipeline
│   ├── database.py                  # SQLite connection and query execution helper
│   ├── db.sqlite                    # Product catalog database (~900 shoes)
│   ├── graph.py                     # Multi-step LangGraph SQL generation pipeline
│   ├── guardrails.py                # SQL security: input sanitization, SELECT-only, redaction
│   ├── products.csv                 # Raw dataset (Flipkart footwear catalog)
│   ├── prompts.py                   # Catalog schema instructions for Groq LLM
│   ├── seed_data.py                 # Loads products.csv into db.sqlite
│   └── server.py                    # FastAPI microservice running on port 8002
│
├──  rag/                          # Semantic Policy & FAQ Retrieval Engine
│   ├── chroma_db/                # Local persistent Chroma vector store
│   ├── faq.csv                      # Store policies, returns, refunds, and shipping Q&As
│   ├── ingest.py                    # Embeds faq.csv using all-MiniLM-L6-v2 into ChromaDB
│   └── retriever.py                 # Vector similarity search interface
│
├──  tools/                        # External Live Search & Knowledge Tools
│   ├── arxiv_tool.py                # ArXiv academic research search wrapper
│   ├── web_search.py                # Live web queries via DuckDuckGo
│   └── wikipedia_tool.py            # Encyclopedic definitions and brand history
│
├── .env                             # Environment configuration (GROQ_API_KEY, GROQ_MODEL)
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules (.venv, dist, .env, chroma_db, etc.)
├── pyproject.toml                   # Root UV workspace definition
├── uv.lock                          # Locked dependencies snapshot
├── README.md                        # Documentation and setup guide
└── Technical_Design_Document.md     # Architecture specifications

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
