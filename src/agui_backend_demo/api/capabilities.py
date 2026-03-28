from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

AGENT_CAPABILITIES = {
    "segment": {
        "streaming": True,
        "state": True,
        "tools": False,
        "reasoning": False,
        "activity": False,
        "human_in_loop": False,
    },
    "template": {
        "streaming": True,
        "state": True,
        "tools": True,
        "reasoning": True,
        "activity": True,
        "human_in_loop": True,
    },
    "chat": {
        "streaming": True,
        "state": False,
        "tools": True,
        "reasoning": False,
        "activity": False,
        "multi_agent": True,
    },
    "campaign": {
        "streaming": True,
        "state": True,
        "tools": False,
        "reasoning": False,
        "activity": False,
    },
    "custom_property": {
        "streaming": True,
        "state": True,
        "tools": False,
        "reasoning": False,
        "custom_events": True,
    },
}


@router.get("/agents/capabilities")
async def get_capabilities():
    return AGENT_CAPABILITIES
