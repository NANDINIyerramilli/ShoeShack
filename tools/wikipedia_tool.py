import wikipedia as _wikipedia
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

_wikipedia.set_user_agent(
    "ecomm-chatbot/0.1 (https://github.com/Harish369/ecomm-chatbot)"
)

api_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=2000)

wikipedia_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
