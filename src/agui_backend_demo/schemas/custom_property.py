from pydantic import BaseModel


class CustomProperty(BaseModel):
    name: str
    description: str
    javascript_code: str
    property_type: str = "string"  # string, number, boolean, date
    example_value: str | None = None
