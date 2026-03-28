from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from agui_backend_demo.agent.chat.tools import (
    create_template,
    generate_custom_property,
    generate_segment,
)

SYSTEM_PROMPT = """\
You are a helpful AI assistant for an email marketing platform. You have access \
to specialized tools for:

1. **Segment Generation** - Create audience segments with targeting conditions
2. **Template Creation** - Design professional HTML email templates
3. **Custom Properties** - Generate computed user properties with JavaScript code

Use these tools when the user's request matches their purpose. For general \
questions, answer directly without tools. Be concise and helpful.\
"""


def build_chat_agent(model: str = "claude-sonnet-4-20250514"):
    """Build a chat agent with multi-agent orchestration tools."""
    llm = ChatAnthropic(model=model)
    return create_react_agent(
        llm,
        tools=[generate_segment, create_template, generate_custom_property],
        prompt=SYSTEM_PROMPT,
    )
