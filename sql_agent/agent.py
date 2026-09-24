from graph import graph


def run_agent(query: str) -> str:
    result = graph.invoke({"query": query})
    return result.get("response", "")
