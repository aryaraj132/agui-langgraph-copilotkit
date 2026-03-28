from typing import TypedDict


class CustomPropertyState(TypedDict):
    messages: list
    custom_property: dict | None
    error: str | None
