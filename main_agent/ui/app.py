import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from main_agent.graph import graph

st.set_page_config(page_title="ShoeShack", page_icon="👟", layout="centered")
st.title("👟 ShoeShack")
st.caption("Your AI Assistant for shoe collections, orders, and customer support")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = "user_1"

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.sidebar.title("Settings")
st.session_state.user_id = st.sidebar.text_input("User ID", st.session_state.user_id)
st.sidebar.write(f"Session: {st.session_state.session_id}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Ask ShoeShack about shoes, orders, complaints, FAQs…")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking… 🤖"):
            try:
                result = graph.invoke(
                    {"query": query, "user_id": st.session_state.user_id}
                )
                response = result.get("response") or "No response."
            except Exception as e:
                response = f"Error: {e}"
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
