import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from main_agent.tools import ALL_TOOLS
from main_agent.prompts import SYSTEM_PROMPT

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

_react_agent = None


def get_agent():
    global _react_agent
    if _react_agent is not None:
        return _react_agent

    load_dotenv(PROJECT_ROOT / ".env", override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please add GROQ_API_KEY to your .env file.")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    llm = ChatGroq(model=model, temperature=0, api_key=api_key)
    _react_agent = create_react_agent(llm, ALL_TOOLS)
    return _react_agent


def run(query: str, user_id: str = "user_1") -> dict:
    """Invoke the ReAct agent with a single user query."""
    system_message = SystemMessage(content=SYSTEM_PROMPT.format(user_id=user_id))
    agent = get_agent()
    result = agent.invoke(
        {"messages": [system_message, ("user", query)]}
    )
    messages = result.get("messages", [])
    final_message = messages[-1] if messages else None
    response = getattr(final_message, "content", "") if final_message else ""
    return {"messages": messages, "response": response}


graph = type("GraphFacade", (), {"invoke": staticmethod(
    lambda payload: run(payload["query"], payload.get("user_id", "user_1"))
)})()
