"""Backend tools for the chat agent to orchestrate other agents.

Each tool invokes a specialized agent graph and returns its result as JSON.
Imports are deferred to avoid circular dependencies.
"""

import json

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool


@tool
async def generate_segment(description: str) -> str:
    """Generate a user segment based on a description. Use this when the user
    wants to create audience segments for targeting."""
    from agui_backend_demo.agent.segment.graph import build_segment_graph

    graph = build_segment_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=description)],
            "segment": None,
            "error": None,
        }
    )
    if result.get("error"):
        return json.dumps({"error": result["error"]})
    return result["segment"].model_dump_json()


@tool
async def create_template(brief: str) -> str:
    """Create an email template based on a brief. Use this when the user
    wants to create or design an email template."""
    from agui_backend_demo.agent.template.graph import build_template_graph

    graph = build_template_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=brief)],
            "template": None,
            "error": None,
            "version": 0,
        }
    )
    if result.get("error"):
        return json.dumps({"error": result["error"]})
    return json.dumps(result["template"])


@tool
async def generate_custom_property(description: str) -> str:
    """Generate a custom user property with JavaScript code. Use this when the
    user wants to create computed properties for segmentation."""
    from agui_backend_demo.agent.custom_property.graph import (
        build_custom_property_graph,
    )

    graph = build_custom_property_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=description)],
            "custom_property": None,
            "error": None,
        }
    )
    if result.get("error"):
        return json.dumps({"error": result["error"]})
    return json.dumps(result["custom_property"])
