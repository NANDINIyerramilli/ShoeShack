import asyncio
import os

import requests
from langchain_core.tools import tool
from fastmcp import Client

from rag.retriever import search_faq as _search_faq
from tools.web_search import web_search_tool
from tools.wikipedia_tool import wikipedia_tool
from tools.arxiv_tool import arxiv_tool

SQL_AGENT_URL = os.getenv("SQL_AGENT_URL", "http://localhost:8002/invoke")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/sse")


@tool
def search_faq(query: str) -> str:
    """Semantic search over the ecommerce FAQ knowledge base.

    Use this for questions about returns, refunds, shipping, payments, promo codes,
    tracking, and other policy questions.
    """
    return _search_faq(query)


@tool
def web_search(query: str) -> str:
    """Search the public web via DuckDuckGo for current or general information."""
    return web_search_tool.run(query)


@tool
def wikipedia(query: str) -> str:
    """Look up general knowledge and definitions on Wikipedia."""
    return wikipedia_tool.run(query)


@tool
def arxiv(query: str) -> str:
    """Search ArXiv for academic and research papers on a topic."""
    return arxiv_tool.run(query)


@tool
def call_sql_agent(query: str, user_id: str) -> str:
    """Query the ecommerce product catalog in natural language.

    Use for product searches, price/stock/category lookups, recommendations.
    Example: "show shoes under 5000".
    """
    try:
        print('sql:', query)
        response = requests.post(
            SQL_AGENT_URL,
            json={"query": query, "user_id": user_id},
            timeout=30,
        )
        print(response)
        response.raise_for_status()

        print(str(response.json().get("response", response.json())))
        return str(response.json().get("response", response.json()))
    except Exception as e:
        return f"SQL agent error: {e}"


def _run_mcp_tool(tool_name: str, user_id: str) -> str:
    async def _call():
        async with Client(MCP_SERVER_URL) as client:
            result = await client.call_tool(tool_name, {"user_id": user_id})
            return result

    try:
        result = asyncio.run(_call())
        if hasattr(result, "data") and result.data is not None:
            return str(result.data)
        if hasattr(result, "content") and result.content:
            return "\n".join(getattr(c, "text", str(c)) for c in result.content)
        return str(result)
    except Exception as e:
        return f"MCP error calling {tool_name}: {e}"


@tool
def get_orders(user_id: str) -> str:
    """Fetch all orders for the given user from the MCP server."""
    return _run_mcp_tool("fetch_orders", user_id)


@tool
def get_complaints(user_id: str) -> str:
    """Fetch all support complaint tickets for the given user from the MCP server."""
    return _run_mcp_tool("fetch_complaints", user_id)


ALL_TOOLS = [
    search_faq,
    web_search,
    wikipedia,
    arxiv,
    call_sql_agent,
    get_orders,
    get_complaints,
]
