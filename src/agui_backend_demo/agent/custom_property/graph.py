from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.custom_property.state import CustomPropertyState
from agui_backend_demo.schemas.custom_property import CustomProperty

SYSTEM_PROMPT = """\
You are a custom property generator for an email marketing platform. \
Given a description, generate a custom user property definition with:
1. A snake_case property name
2. A clear description
3. JavaScript code that computes the property value from a user object
4. The property type (string, number, boolean, or date)
5. An example value

The JavaScript code should be a function body that has access to a `user` \
object with fields like: signup_date, login_count, purchase_count, \
total_spent, last_login_date, email_opened, country, plan_type.
"""


def _build_generate_node(llm):
    structured_llm = llm.with_structured_output(CustomProperty)

    async def generate_property(state: CustomPropertyState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {"custom_property": result.model_dump(), "error": None}
        except Exception as e:
            return {"custom_property": None, "error": str(e)}

    return generate_property


def build_custom_property_graph(model: str = "claude-sonnet-4-20250514"):
    llm = ChatAnthropic(model=model)
    graph = StateGraph(CustomPropertyState)
    graph.add_node("generate_property", _build_generate_node(llm))
    graph.add_edge(START, "generate_property")
    graph.add_edge("generate_property", END)
    return graph.compile()
