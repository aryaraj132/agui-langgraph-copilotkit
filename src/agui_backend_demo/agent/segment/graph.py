from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.segment.state import SegmentAgentState
from agui_backend_demo.schemas.segment import Segment

SYSTEM_PROMPT = """\
You are a user segmentation expert. Given a natural language description, \
generate a structured segment definition.

## Available Field Types

- **User properties**: age, gender, country, city, language, signup_date, \
plan_type, account_status
- **Behavioral events**: purchase_count, last_purchase_date, total_spent, \
login_count, last_login_date, page_views, session_duration
- **Engagement**: email_opened, email_clicked, push_notification_opened, \
app_opens, feature_used
- **Custom attributes**: any user-defined property (use descriptive snake_case names)

## Available Operators

- **Comparison**: equals, not_equals, greater_than, less_than, \
greater_than_or_equal, less_than_or_equal
- **String**: contains, not_contains, starts_with, ends_with
- **Temporal**: within_last, before, after, between
- **Existence**: is_set, is_not_set
- **List**: in, not_in

## Rules

1. Generate a concise, descriptive segment name.
2. Write a clear human-readable description of who this segment targets.
3. Group conditions logically using AND/OR groups.
4. Use the most specific field and operator that matches the user's intent.
5. For temporal values, use clear formats like "30 days", "2024-01-01", etc.
6. If the query implies multiple independent criteria, use separate condition \
groups joined appropriately.
7. Set estimated_scope to a brief description of the expected audience size \
or reach (e.g., "Users matching all activity and location criteria").
"""


def _build_generate_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(Segment)

    async def generate_segment(state: SegmentAgentState) -> dict:
        try:
            # Extract the last user message content
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
            return {"segment": result, "error": None}
        except Exception as e:
            return {"segment": None, "error": str(e)}

    return generate_segment


def build_segment_graph(model: str = "claude-sonnet-4-20250514"):
    """Build and compile the segment generation graph."""
    llm = ChatAnthropic(model=model)

    graph = StateGraph(SegmentAgentState)
    graph.add_node("generate_segment", _build_generate_node(llm))
    graph.add_edge(START, "generate_segment")
    graph.add_edge("generate_segment", END)

    return graph.compile()
