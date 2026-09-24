from fastmcp import FastMCP
from database import get_orders, get_complaints

mcp = FastMCP("Ecommerce MCP Server")


@mcp.tool()
def fetch_orders(user_id: str):
    """Fetch all orders for a user."""
    return get_orders(user_id)


@mcp.tool()
def fetch_complaints(user_id: str):
    """Fetch all complaints for a user."""
    return get_complaints(user_id)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8001)