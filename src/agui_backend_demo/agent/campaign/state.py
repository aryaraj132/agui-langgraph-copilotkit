from typing import TypedDict


class CampaignState(TypedDict):
    messages: list
    campaign: dict | None
    segment: dict | None
    template: dict | None
    error: str | None
