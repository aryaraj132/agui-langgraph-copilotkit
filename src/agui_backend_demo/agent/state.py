from typing import TypedDict

from agui_backend_demo.schemas.segment import Segment


class SegmentAgentState(TypedDict):
    messages: list
    segment: Segment | None
    error: str | None
