from pydantic import BaseModel


class Campaign(BaseModel):
    name: str
    segment_id: str | None = None
    template_id: str | None = None
    subject: str = ""
    send_time: str | None = None
    status: str = "draft"
