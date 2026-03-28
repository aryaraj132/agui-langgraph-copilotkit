FRONTEND_TOOLS = [
    {
        "name": "update_section",
        "description": "Update the content of an existing template section",
        "parameters": {
            "type": "object",
            "properties": {
                "section_id": {
                    "type": "string",
                    "description": "The ID of the section to update",
                },
                "content": {
                    "type": "string",
                    "description": "The new HTML content for the section",
                },
            },
            "required": ["section_id", "content"],
        },
    },
    {
        "name": "add_section",
        "description": "Add a new section to the email template",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": (
                        "Section type: header, body, footer, cta, or image"
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "The HTML content for the new section",
                },
                "position": {
                    "type": "integer",
                    "description": "Position index to insert at (0-based)",
                },
            },
            "required": ["type", "content"],
        },
    },
    {
        "name": "remove_section",
        "description": "Remove a section from the email template",
        "parameters": {
            "type": "object",
            "properties": {
                "section_id": {
                    "type": "string",
                    "description": "The ID of the section to remove",
                },
            },
            "required": ["section_id"],
        },
    },
]


def get_frontend_tool_schemas() -> list[dict]:
    """Return the list of frontend-defined tool schemas."""
    return FRONTEND_TOOLS
