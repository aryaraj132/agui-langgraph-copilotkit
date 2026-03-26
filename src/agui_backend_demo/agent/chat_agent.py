from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = """\
You are a friendly, helpful AI assistant. Answer the user's questions clearly \
and concisely. If you don't know something, say so honestly.\
"""


def build_chat_agent(model: str = "claude-sonnet-4-20250514"):
    """Build a generic chat agent using create_react_agent."""
    llm = ChatAnthropic(model=model)
    return create_react_agent(llm, tools=[], prompt=SYSTEM_PROMPT)
