import os
import re
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from guardrails import validate_input, validate_output, validate_sql
from database import execute_query
from prompts import SQL_SYSTEM_PROMPT

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
class SQLState(TypedDict, total=False):
    query: str
    sql: str
    rows: list
    response: str


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    tagged = re.search(r"<SQL>\s*(.*?)\s*</SQL>", text, re.DOTALL | re.IGNORECASE)
    if tagged:
        return tagged.group(1).strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return text


def input_guardrails(state: SQLState) -> SQLState:
    validate_input(state["query"])
    return state


def sql_generator(state: SQLState) -> SQLState:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in .env. Please configure GROQ_API_KEY.")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    llm = ChatGroq(model=model, temperature=0, api_key=api_key)
    response = llm.invoke([
        SystemMessage(content=SQL_SYSTEM_PROMPT),
        HumanMessage(content=state["query"]),
    ])
    raw = response.content if hasattr(response, "content") else str(response)
    state["sql"] = _strip_code_fences(raw)
    return state


def query_executor(state: SQLState) -> SQLState:
    safe_sql = validate_sql(state["sql"])
    state["sql"] = safe_sql
    state["rows"] = execute_query(safe_sql)
    return state


def output_guardrails(state: SQLState) -> SQLState:
    state["rows"] = validate_output(state["rows"])
    return state


def response_formatter(state: SQLState) -> SQLState:
    rows = state["rows"]
    if not rows:
        state["response"] = "No products found."
    else:
        state["response"] = str(rows)
    return state


graph_builder = StateGraph(SQLState)
graph_builder.add_node("input_guardrails", input_guardrails)
graph_builder.add_node("sql_generator", sql_generator)
graph_builder.add_node("query_executor", query_executor)
graph_builder.add_node("output_guardrails", output_guardrails)
graph_builder.add_node("response_formatter", response_formatter)

graph_builder.set_entry_point("input_guardrails")
graph_builder.add_edge("input_guardrails", "sql_generator")
graph_builder.add_edge("sql_generator", "query_executor")
graph_builder.add_edge("query_executor", "output_guardrails")
graph_builder.add_edge("output_guardrails", "response_formatter")
graph_builder.add_edge("response_formatter", END)

graph = graph_builder.compile()
