from typing import TypedDict


class TemplateAgentState(TypedDict):
    messages: list
    template: dict | None
    error: str | None
    version: int
