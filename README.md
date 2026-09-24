# 👟 ShoeShack — Enterprise Agentic RAG with MCP Ecommerce Platform

An enterprise-grade multi-agent RAG and customer intelligence platform built for modern ecommerce. ShoeShack combines a **LangGraph ReAct orchestrator**, a **FastMCP Model Context Protocol server**, a dedicated **NL-to-SQL agent with query guardrails**, and **semantic FAQ retrieval via ChromaDB**, accessible through both a sleek **React Web UI** and a **Streamlit application**.

---

## 🏗️ Architecture Overview

```text
                       ┌─────────────────────────────────────────┐
                       │               User Client               │
                       │   React Web UI (:8000) / Streamlit (:8501)│
                       └────────────────────┬────────────────────┘
                                            │ HTTP / JSON
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │         Main Orchestrator Agent         │
                       │        FastAPI + LangGraph ReAct        │
                       │           (Groq LLM Engine)             │
                       └────────────────────┬────────────────────┘
                                            │
         ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
         │                  │                               │                  │
         ▼                  ▼                               ▼                  ▼
  ┌─────────────┐    ┌──────────────┐                ┌─────────────┐    ┌──────────────┐
  │ MCP Server  │    │  SQL Agent   │                │  RAG Engine │    │  Live Tools  │
  │ Orders &    │    │  Product DB  │                │  Policy FAQ │    │  DuckDuckGo  │
  │ Complaints  │    │  NL → SQL    │                │  ChromaDB   │    │  Wikipedia   │
  │ SSE :8001   │    │  HTTP :8002  │                │  MiniLM-L6  │    │  ArXiv       │
  └──────┬──────┘    └──────┬───────┘                └─────────────┘    └──────────────┘
         ▼                  ▼
  SQLite (orders/    SQLite (catalog
   complaints)        ~900 shoes)
```
<img width="825" height="552" alt="Screenshot 2026-09-24 232212" src="https://github.com/user-attachments/assets/9f148896-ec89-46b7-9e85-da8bbfdc9c4b" />
<img width="1916" height="856" alt="Screenshot 2026-09-24 222515" src="https://github.com/user-attachments/assets/6c8a341f-5a0f-4d22-83ca-108234d24902" />
<img width="763" height="681" alt="Screenshot 2026-09-24 222655" src="https://github.com/user-attachments/assets/c298b8e8-054d-42de-ab6d-e2d4e9c1eebe" />
<img width="1828" height="861" alt="Screenshot 2026-09-24 222721" src="https://github.com/user-attachments/assets/3e3e35d7-338a-4fce-b7ef-8b19ffcaf90d" />

---

## 🌟 Key Capabilities

| Tool | Backend & Transport | Primary Purpose |
| :--- | :--- | :--- |
| **`call_sql_agent`** | HTTP POST (`:8002`) → SQLite | Natural language queries for sneakers, prices, brands, ratings, and discounts. |
| **`get_orders`** | FastMCP Client (SSE `:8001`) | Fetches real-time customer order history and order tracking status. |
| **`get_complaints`** | FastMCP Client (SSE `:8001`) | Looks up active customer support tickets, status, and priorities. |
| **`search_faq`** | ChromaDB + `all-MiniLM-L6-v2` | Dense vector semantic search for store policies, shipping, returns, and refunds. |
| **`web_search`** | DuckDuckGo Search API | Fetches live public web information and external current deals. |
| **`wikipedia`** | Wikipedia API Wrapper | Encyclopedic queries, brand histories, and sneaker culture knowledge. |
| **`arxiv`** | ArXiv Search Client | Research papers on recommendation systems, materials, and algorithms. |

---

## 🛠️ Technology Stack

- **Orchestration**: [LangChain](https://www.langchain.com/), [LangGraph](https://github.com/langchain-ai/langgraph) (ReAct loop)
- **Language Models**: [Groq](https://groq.com/) (`openai/gpt-oss-120b` or `llama-3.3-70b-versatile`)
- **Protocol**: [FastMCP](https://github.com/jlowin/fastmcp) (Server-Sent Events)
- **Databases**: SQLite (Product catalog & orders/tickets)
- **Vector Store**: [ChromaDB](https://www.trychroma.com/) with Sentence Transformers (`all-MiniLM-L6-v2`)
- **Backends**: [FastAPI](https://fastapi.tiangolo.com/), Uvicorn
- **Frontends**:
  - Modern React 18 + Vite (Responsive chat dock, dark aesthetic, live link previews)
  - Streamlit (Fast prototyping & debug dashboard)
- **Package Management**: [Astral UV](https://docs.astral.sh/uv/) workspace

---

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+** & **npm** (for building or developing the frontend)
- **[UV package manager](https://astral.sh/uv/)**
- **Groq API Key** ([Get one here](https://console.groq.com/keys))

Install UV:
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## ⚙️ Installation & Setup

### 1. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Optional LangSmith Tracing
LANGCHAIN_TRACING_V2=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=enterprise-rag
```

### 2. Install Python Dependencies

Using `uv`, sync all dependencies across workspace packages:

```bash
uv sync
```

### 3. Seed Databases & Ingest FAQ Knowledge Base

```bash
# Seed MCP orders and complaints database
uv run python mcp_server/seed_data.py

# Seed SQLite product catalog from products.csv (~900 items)
uv run python sql_agent/seed_data.py

# Ingest FAQ into ChromaDB vector store
uv run python rag/ingest.py
```

### 4. Build Frontend (React / Vite)

```bash
cd frontend
npm install
npm run build
cd ..
```

The compiled assets are placed into `frontend/dist/` and served automatically by the FastAPI backend on port 8000.

---

## 🚀 Running the Platform

To run the complete platform, start the three core microservices in separate terminals:

### Terminal 1 — MCP Server (Port 8001, SSE)
```bash
uv run python mcp_server/server.py
```
*Listens on `http://localhost:8001/sse`*

### Terminal 2 — SQL Agent Service (Port 8002, HTTP)
```bash
uv run python sql_agent/server.py
```
*Listens on `http://localhost:8002`*

### Terminal 3 — Main Agent API & React Web UI (Port 8000)
```bash
uv run python -m uvicorn main_agent.api:app --host 0.0.0.0 --port 8000
```
*Open your browser at **`http://localhost:8000`** to access the web application!*

---

### Alternative Interfaces

- **Streamlit Interface** (Port 8501):
  ```bash
  uv run streamlit run main_agent/ui/app.py --server.port 8501
  ```
  *Accessible at `http://localhost:8501`*

- **Frontend Hot-Reload Dev Server** (Port 3000):
  ```bash
  cd frontend && npm run dev
  ```
  *Proxies API requests to `http://localhost:8000`*

- **CLI Direct Chat**:
  ```bash
  uv run python -m main_agent.agent
  ```

---

## 🔒 Security & SQL Guardrails

The SQL Agent uses a multi-tier safety pipeline before queries ever execute against the database:

```text
User Natural Language Query
          │
          ▼
   [input_guardrails]   ──► Blocks DROP, DELETE, UPDATE, INSERT, ALTER, UNION, comments (--)
          │
          ▼
   [sql_generator]      ──► Generates strict single-statement SELECT via Groq LLM
          │
          ▼
   [query_executor]     ──► Validates SQL AST; executes read-only query
          │
          ▼
  [output_guardrails]   ──► Enforces MAX_ROWS (5) & redacts sensitive fields
          │
          ▼
 [response_formatter]   ──► Structured markdown output with direct links
```

---

## 💬 Sample User Queries

| Intent | Sample Prompt | Dispatched Tool |
| :--- | :--- | :--- |
| **Product Discovery** | *"Find Campus running shoes under ₹1500"* | `call_sql_agent` |
| **Catalog Details** | *"Show me top-rated Nike sneakers with discount"* | `call_sql_agent` |
| **Order Status** | *"What is the status of my recent orders?"* | `get_orders` |
| **Customer Support** | *"Do I have any open support complaints?"* | `get_complaints` |
| **Policy Questions** | *"What is your return and refund window?"* | `search_faq` |
| **Current Deals** | *"What are the best current sneaker deals?"* | `web_search` |
| **Sneaker History** | *"Who founded Nike and in which year?"* | `wikipedia` |

---

## 📁 Project Structure

```text
Enterprise-Agentic-RAG-Ecomm-Chatbot/
├── .env.example                     # Environment template
├── pyproject.toml                   # Root UV workspace configuration
├── README.md                        # Documentation
├── Technical_Design_Document.md     # Architecture specifications
│
├── frontend/                        # Modern React + Vite Web UI
│   ├── dist/                        # Production build bundle
│   ├── public/                      # Static assets (background image)
│   ├── src/
│   │   ├── App.jsx                  # Main chat interface component
│   │   ├── index.css                # Dark editorial glassmorphism styling
│   │   └── main.jsx                 # React root mount
│   ├── package.json
│   └── vite.config.js               # Dev server proxy configuration
│
├── main_agent/                      # Orchestration service
│   ├── agent.py                     # CLI interactive loop
│   ├── api.py                       # FastAPI entrypoint (serves API & dist)
│   ├── graph.py                     # ReAct orchestrator loop & caching
│   ├── prompts.py                   # System prompt & tool routing rules
│   ├── tools.py                     # Tool definitions & MCP client integration
│   └── ui/                          # Streamlit application
│       └── app.py
│
├── mcp_server/                      # FastMCP Service
│   ├── database.py                  # Orders & complaints queries
│   ├── models.py                    # Data schemas
│   ├── orders_complaints.db         # SQLite storage for orders and tickets
│   ├── seed_data.py                 # Mock data generator (Faker)
│   └── server.py                    # FastMCP SSE server (:8001)
│
├── sql_agent/                       # NL-to-SQL Product Catalog Agent
│   ├── agent.py                     # Service invocation wrapper
│   ├── database.py                  # SQLite query executor
│   ├── db.sqlite                    # Shoes catalog database (~900 rows)
│   ├── graph.py                     # LangGraph SQL pipeline
│   ├── guardrails.py                # SQL validation, AST checks, redactions
│   ├── products.csv                 # Raw catalog source
│   ├── prompts.py                   # Schema instructions
│   ├── seed_data.py                 # CSV -> SQLite seeder
│   └── server.py                    # FastAPI service (:8002)
│
├── rag/                             # Semantic Retrieval Engine
│   ├── chroma_db/                   # Chroma vector embeddings store
│   ├── faq.csv                      # Ecommerce policy Q&A dataset
│   ├── ingest.py                    # Embedding indexing script
│   └── retriever.py                 # SentenceTransformer vector retriever
│
└── tools/                           # Live External Tools
    ├── arxiv_tool.py                # Academic paper retrieval
    ├── web_search.py                # DuckDuckGo integration
    └── wikipedia_tool.py            # Wikipedia knowledge retrieval
```

---

## 🛠️ API Reference

### Main Service (`:8000`)
- **`GET /api/health`**: Health status check.
  ```json
  {"status": "ok", "app": "ShoeShack"}
  ```
- **`POST /api/chat`**: Send messages to the ReAct agent.
  ```json
  {
    "query": "Show running shoes under 2000",
    "user_id": "user_1"
  }
  ```

### SQL Agent (`:8002`)
- **`POST /invoke`**: Direct NL query to catalog pipeline.
  ```json
  {
    "query": "Show Nike shoes",
    "user_id": "user_1"
  }
  ```

### MCP Service (`:8001`)
- **`GET /sse`**: FastMCP Server-Sent Events endpoint for tool execution.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
