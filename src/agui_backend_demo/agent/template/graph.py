import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.template.state import TemplateAgentState
from agui_backend_demo.schemas.template import EmailTemplate

GENERATE_SYSTEM_PROMPT = """\
You are an expert email template designer. Given a user's description, \
generate a professional HTML email template.

## Output Requirements

- A clear, descriptive subject line.
- A short preview text (the snippet shown in email clients).
- Fully self-contained HTML with **inline CSS** (email clients strip \
<style> blocks).
- Use a 600px centered container for maximum compatibility.
- Include sections such as header, body, CTA (call-to-action), and footer.
- Each section must have a unique ``id`` (e.g. "s1", "s2"), a ``type`` \
(header | body | cta | footer | image), and its HTML ``content``.
- Keep the design responsive using percentage-based widths inside the \
600px container.
- Use web-safe fonts (Arial, Helvetica, Georgia, etc.).
"""

MODIFY_SYSTEM_PROMPT = """\
You are an expert email template designer. The user has an existing \
template and wants to modify it.

## Current Template

Subject: {subject}
Sections: {sections}

Full HTML:
{html}

## Instructions

Apply the user's requested changes to the template. Preserve any \
sections not mentioned. Return the complete updated template with all \
sections.
"""


def _build_generate_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(EmailTemplate)

    async def generate_template(state: TemplateAgentState) -> dict:
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
                SystemMessage(content=GENERATE_SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {
                "template": result.model_dump(),
                "error": None,
                "version": 1,
            }
        except Exception as e:
            return {"template": None, "error": str(e)}

    return generate_template


def _build_modify_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(EmailTemplate)

    async def modify_template(state: TemplateAgentState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

            existing = state.get("template") or {}
            sections_summary = json.dumps(
                [
                    {"id": s.get("id"), "type": s.get("type")}
                    for s in existing.get("sections", [])
                ]
            )

            system_content = MODIFY_SYSTEM_PROMPT.format(
                subject=existing.get("subject", ""),
                sections=sections_summary,
                html=existing.get("html", ""),
            )

            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            current_version = state.get("version", 0)
            return {
                "template": result.model_dump(),
                "error": None,
                "version": current_version + 1,
            }
        except Exception as e:
            return {"template": state.get("template"), "error": str(e)}

    return modify_template


def _route_by_state(state: TemplateAgentState) -> str:
    """Route to generate or modify based on whether a template exists."""
    if state.get("template") is None:
        return "generate_template"
    return "modify_template"


def build_template_graph(model: str = "claude-sonnet-4-20250514"):
    """Build and compile the template generation/modification graph."""
    llm = ChatAnthropic(model=model)

    graph = StateGraph(TemplateAgentState)
    graph.add_node("generate_template", _build_generate_node(llm))
    graph.add_node("modify_template", _build_modify_node(llm))
    graph.add_conditional_edges(START, _route_by_state)
    graph.add_edge("generate_template", END)
    graph.add_edge("modify_template", END)

    return graph.compile()
