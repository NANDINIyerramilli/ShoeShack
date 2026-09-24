# Enterprise Agentic RAG Ecommerce Chatbot

## Technical Design Document (TDD)

---

# 1. Overview

## Objective

Build an enterprise-grade Agentic RAG-based Ecommerce Chatbot using:

* LangChain
* LangGraph
* LangSmith
* Python 3.11
* ChromaDB
* MCP Server Architecture
* Agent-to-Agent (A2A) communication
* SQLite
* GROQ LLMs
* UV package management

The system must support:

* FAQ retrieval via RAG
* Ecommerce SQL querying
* Order and complaint retrieval via MCP
* External knowledge retrieval:

  * DuckDuckGo
  * Wikipedia
  * ArXiv
* Multi-agent orchestration
* Independent service deployment

---

# 2. High-Level Architecture

```text
                           ┌────────────────────┐
                           │    User Client     │
                           └─────────┬──────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │      Main Orchestrator Agent   │
                    │        (LangGraph ReAct)       │
                    └──────────────┬─────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼

┌───────────────┐      ┌──────────────────┐      ┌───────────────────┐
│  MCP Server   │      │   SQL Agent      │      │  RAG Retriever    │
│ Orders/Tickets│      │ Product DB Agent │      │    ChromaDB       │
└──────┬────────┘      └────────┬─────────┘      └─────────┬─────────┘
       │                        │                           │
       ▼                        ▼                           ▼
SQLite Orders DB        SQLite Product DB          FAQ Embeddings

        ┌────────────────────────────────────────────────────┐
        │                External Knowledge Tools            │
        │ DuckDuckGo | Wikipedia | ArXiv                    │
        └────────────────────────────────────────────────────┘
```

---

# 3. Repository Structure

```text
ecomm_chatbot/
│
├── pyproject.toml
├── uv.lock
├── .env
├── README.md
├── Technical_Design_Document.md
├── main.py
│
├── mcp_server/
│   ├── pyproject.toml
│   ├── server.py
│   ├── database.py
│   ├── seed_data.py
│   ├── models.py
│   └── orders_complaints.db
│
├── sql_agent/
│   ├── pyproject.toml
│   ├── server.py
│   ├── agent.py
│   ├── graph.py
│   ├── guardrails.py
│   ├── prompts.py
│   ├── database.py
│   ├── seed_data.py
│   ├── products.csv
│   └── db.sqlite
│
├── rag/
│   ├── pyproject.toml
│   ├── faq.csv
│   ├── ingest.py
│   ├── retriever.py
│   └── chroma_db/
│
├── tools/
│   ├── pyproject.toml
│   ├── web_search.py
│   ├── wikipedia_tool.py
│   └── arxiv_tool.py
│
└── main_agent/
    ├── pyproject.toml
    ├── agent.py
    ├── graph.py
    ├── tools.py
    ├── prompts.py
    └── ui/
        └── app.py
```

---

# 4. Technology Stack

| Layer            | Technology       |
| ---------------- | ---------------- |
| Language         | Python 3.11      |
| Package Manager  | UV               |
| Agent Framework  | LangGraph        |
| LLM Framework    | LangChain        |
| Observability    | LangSmith        |
| LLM Provider     | GROQ             |
| Vector DB        | ChromaDB         |
| Embedding Model  | all-MiniLM-L6-v2 |
| Databases        | SQLite           |
| MCP Protocol     | FastMCP          |
| API Layer        | FastAPI          |
| Transport        | SSE + HTTP       |
| External Search  | DuckDuckGo       |
| Knowledge Source | Wikipedia        |
| Research Source  | ArXiv            |

---

# 5. Environment Variables

```env
GROQ_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
LANGCHAIN_TRACING_V2=true

GROQ_MODEL=openai/gpt-oss-120b
```

---

# 6. MCP Server Design

## Purpose

Provide operational customer data:

* Orders
* Complaints/Tickets

## Responsibilities

* Expose MCP tools
* Query SQLite DB
* Return structured JSON

## Database Schema

### orders

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    product TEXT,
    status TEXT,
    amount REAL,
    created_at TEXT
);
```

### tickets

```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    subject TEXT,
    description TEXT,
    status TEXT,
    priority TEXT,
    created_at TEXT
);
```

## MCP Tools

### get_orders(user_id)

Returns all orders for a user.

### get_complaints(user_id)

Returns all complaint tickets for a user.

## Transport

* SSE (Server Sent Events)

## Startup

```bash
uv run --package mcp_server python server.py
```

---

# 7. SQL Agent Design

## Purpose

Handle natural language SQL querying over ecommerce catalog data.

## Responsibilities

* Accept NL queries
* Generate SQL safely
* Execute queries
* Return guarded responses

## A2A Boundary

HTTP endpoint:

```http
POST /invoke
```

Request:

```json
{
  "query": "show all laptops under 50000",
  "user_id": "u1001"
}
```

## Internal LangGraph Pipeline

```text
[input_guardrails]
        ↓
[sql_generator]
        ↓
[query_executor]
        ↓
[output_guardrails]
        ↓
[response_formatter]
```

---

# 8. SQL Guardrails

## Input Guardrails

Blocked patterns:

* DROP
* DELETE
* UPDATE
* INSERT
* ALTER
* UNION attacks
* SQL comments
* Multiple statements

## Output Guardrails

* Max rows = 20 (sized to fit Groq free-tier 8k TPM window)
* Drop `product_link` — Flipkart URLs are ~500 chars each and dominate token cost
* Strip PII-style fields: `email`, `phone`, `address`, `password`, `user_id`
* Redact any other internal identifiers

---

# 9. SQL Database Schema

## product

Single table in `sql_agent/db.sqlite`, populated from `sql_agent/products.csv`
(~900 rows of Flipkart-sourced shoes / sports footwear).

```sql
CREATE TABLE product (
    "index"        INTEGER,   -- original row id from source export
    product_link   TEXT,      -- canonical Flipkart URL
    title          TEXT,      -- product name
    brand          TEXT,      -- e.g. Nike, Puma, Sparx, Campus
    price          INTEGER,   -- INR
    discount       REAL,      -- fraction; 0.25 means 25% off
    avg_rating     REAL,      -- 0.0–5.0
    total_ratings  INTEGER    -- number of ratings
);

CREATE INDEX ix_product_index ON product ("index");
```

### LLM prompt contract

The schema description in
[sql_agent/prompts.py](sql_agent/prompts.py) is the authoritative
schema-aware system prompt the SQL generator sees. It instructs the LLM to
use `LIKE` (never `ILIKE`) for case-insensitive brand matching and to emit
`SELECT *` so the response formatter has all fields available.

---

# 10. ChromaDB RAG Design

## Purpose

Retrieve FAQ answers using semantic search.

## Embedding Function

```python
SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
```

## Data Source

```csv
question,answer
What is return policy?,Returns accepted within 7 days
...
```

## Collection

```text
ecommerce_faq
```

## Retrieval Flow

```text
User Query
   ↓
Embedding
   ↓
Vector Similarity Search
   ↓
Top-K FAQ Results
```

---

# 11. External Knowledge Tools

## DuckDuckGo

Purpose:

* Web search
* Current information

## Wikipedia

Purpose:

* General knowledge
* Definitions

## ArXiv

Purpose:

* Research papers
* Academic references

---

# 12. Main Orchestrator Agent

## Purpose

Coordinate all tools and agents.

## Architecture

LangGraph ReAct loop.

## State Object

The main agent uses `langgraph.prebuilt.create_react_agent`, which manages its
own `messages` state internally — user code does not need to declare a custom
TypedDict. The orchestrator's public surface is a single
`graph.invoke({"query": ..., "user_id": ...})` call (see
[main_agent/graph.py](main_agent/graph.py)).

Per-request inputs:

| Field    | Source             | Used for                              |
| -------- | ------------------ | ------------------------------------- |
| query    | UI / CLI input     | User message to the ReAct loop        |
| user_id  | UI sidebar / CLI   | Injected into the system prompt; tools pass it to MCP / SQL agent |

---

# 13. Main Agent Toolset

| Tool           | Purpose              |
| -------------- | -------------------- |
| search_faq     | FAQ semantic search  |
| web_search     | Internet search      |
| wikipedia      | General knowledge    |
| arxiv          | Academic papers      |
| call_sql_agent | Product SQL querying |
| get_orders     | Customer orders      |
| get_complaints | Support complaints   |

---

# 14. LangGraph Flow

```text
        ┌────────────┐
        │   reason   │
        └─────┬──────┘
              │
              ▼
        ┌────────────┐
        │    act     │
        └─────┬──────┘
              │
      done? ──┴── no
              │
             yes
              ▼
        ┌────────────┐
        │  respond   │
        └────────────┘
```

---

# 15. LangSmith Integration

## Purpose

Observability and debugging.

## Features

* Trace execution
* Monitor tool calls
* Token tracking
* Latency analysis
* Graph debugging

---

# 16. Security Considerations

## SQL Security

* Read-only queries only
* Regex sanitization
* No multi-statement execution

## API Security

* Request validation
* JSON schema enforcement

## Data Privacy

* Redact PII
* Limit exposure

---

# 17. Scalability Design

## Future Improvements

* PostgreSQL migration
* Redis caching
* Kafka event bus
* Distributed MCP services
* Dedicated vector DB cluster
* Kubernetes deployment

---

# 18. Startup Workflow

## Step 0 — Seed databases

```bash
cd mcp_server && uv run --package mcp_server python seed_data.py && cd ..
cd sql_agent && uv run --package sql_agent python seed_data.py && cd ..
```

The SQL agent seed reads `sql_agent/products.csv` and writes the `product`
table to `sql_agent/db.sqlite`.

## Step 1 — MCP Server (port 8001, SSE)

```bash
cd mcp_server && uv run --package mcp_server python server.py
```

## Step 2 — SQL Agent (port 8002, HTTP)

```bash
cd sql_agent && uv run --package sql_agent python server.py
```

## Step 3 — FAQ Ingestion

```bash
cd rag && uv run --package rag python ingest.py && cd ..
```

## Step 4 — Main Agent (CLI)

```bash
uv run --package main_agent python -m main_agent.agent
```

`agent.py` uses package-relative imports, so it must be invoked with `-m`,
not as a script path.

## Step 5 — Streamlit UI (optional)

```bash
uv run streamlit run main_agent/ui/app.py
```

---

# 19. Example User Flows

## Example 1 — Order Query

User:

```text
Show my orders
```

Flow:

```text
Main Agent
   → MCP Tool
      → SQLite
```

---

## Example 2 — Product Recommendation

User:

```text
Show Nike running shoes under 5000
```

Flow:

```text
Main Agent
   → SQL Agent (HTTP POST /invoke on :8002)
      → input_guardrails
      → sql_generator (GROQ, schema-aware prompt)
      → query_executor (validate_sql + SELECT against `product`)
      → output_guardrails (cap at 20 rows, drop product_link, PII filter)
      → response_formatter
```

---

## Example 3 — FAQ Query

User:

```text
What is your refund policy?
```

Flow:

```text
Main Agent
   → ChromaDB Retriever
```

---

## Example 4 — Research Query

User:

```text
Latest AI recommendation systems papers
```

Flow:

```text
Main Agent
   → ArXiv Tool
```

---

# 20. Deployment Strategy

## Local Development

Independent processes.

## Production Deployment

Recommended:

* Docker Compose
* Kubernetes
* Nginx API Gateway

---

# 21. Recommended Future Enhancements

## Phase 2

* Multi-user authentication
* JWT authorization
* Conversation memory
* Hybrid search
* Reranking
* Human-in-the-loop approvals

## Phase 3

* Multi-modal RAG
* Voice agents
* Event-driven workflows
* Autonomous escalation agents

---

# 22. Conclusion

This architecture provides:

* Modular microservice-style agents
* Enterprise-grade separation of concerns
* Safe SQL generation
* Multi-agent orchestration
* Scalable RAG foundation
* Extensible external knowledge integration

The design is optimized for:

* Maintainability
* Observability
* Security
* Scalability
* Rapid experimentation

End of Document
