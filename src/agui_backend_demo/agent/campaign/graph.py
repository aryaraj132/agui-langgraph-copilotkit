from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.campaign.state import CampaignState
from agui_backend_demo.schemas.campaign import Campaign

SYSTEM_PROMPT = """\
You are an email campaign builder. Given a description, generate a campaign \
definition with name, subject line, and status. This is a stub implementation \
demonstrating multi-agent state composition in AG-UI.
"""


def _build_generate_node(llm):
    structured_llm = llm.with_structured_output(Campaign)

    async def generate_campaign(state: CampaignState) -> dict:
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
            return {"campaign": result.model_dump(), "error": None}
        except Exception as e:
            return {"campaign": None, "error": str(e)}

    return generate_campaign


def build_campaign_graph(model: str = "claude-sonnet-4-20250514"):
    llm = ChatAnthropic(model=model)
    graph = StateGraph(CampaignState)
    graph.add_node("generate_campaign", _build_generate_node(llm))
    graph.add_edge(START, "generate_campaign")
    graph.add_edge("generate_campaign", END)
    return graph.compile()
