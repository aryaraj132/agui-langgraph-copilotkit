from agui_backend_demo.agent.template.routes import _compute_json_patch
from agui_backend_demo.agent.template.state import TemplateAgentState
from agui_backend_demo.agent.template.tools import get_frontend_tool_schemas
from agui_backend_demo.schemas.template import EmailTemplate


def test_template_agent_state_structure():
    state: TemplateAgentState = {
        "messages": [],
        "template": None,
        "error": None,
        "version": 0,
    }
    assert state["version"] == 0


def test_frontend_tool_schemas():
    tools = get_frontend_tool_schemas()
    assert len(tools) == 3
    names = {t["name"] for t in tools}
    assert names == {"update_section", "add_section", "remove_section"}
    for tool in tools:
        assert "description" in tool
        assert "parameters" in tool


def test_email_template_to_state():
    template = EmailTemplate(subject="Hello", html="<h1>Hi</h1>")
    state_dict = template.model_dump()
    assert state_dict["subject"] == "Hello"
    assert state_dict["version"] == 1


def test_compute_json_patch_replace():
    old = {"name": "old", "version": 1}
    new = {"name": "new", "version": 2}
    patch = _compute_json_patch(old, new)
    assert any(op["op"] == "replace" and op["path"] == "/name" for op in patch)


def test_compute_json_patch_add():
    old = {"a": 1}
    new = {"a": 1, "b": 2}
    patch = _compute_json_patch(old, new)
    assert any(op["op"] == "add" and op["path"] == "/b" for op in patch)


def test_compute_json_patch_remove():
    old = {"a": 1, "b": 2}
    new = {"a": 1}
    patch = _compute_json_patch(old, new)
    assert any(op["op"] == "remove" and op["path"] == "/b" for op in patch)


def test_compute_json_patch_no_change():
    old = {"a": 1}
    new = {"a": 1}
    patch = _compute_json_patch(old, new)
    assert patch == []
