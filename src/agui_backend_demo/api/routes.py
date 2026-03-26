import logging
import uuid

from ag_ui.core import (
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/api/v1")

encoder = EventEncoder()


def _get_field(body: dict, snake: str, camel: str, default=None):
    """Get a field accepting both snake_case and camelCase (AG-UI uses camelCase)."""
    return body.get(snake) or body.get(camel) or default


def _extract_user_query(messages: list) -> str:
    """Extract content from the last user message."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part["text"]
            else:
                return content
    return ""


@router.post("/segment")
async def generate_segment(request: Request):
    body = await request.json()
    thread_id = _get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = _get_field(body, "run_id", "runId", str(uuid.uuid4()))
    query = _extract_user_query(body.get("messages", []))

    segment_graph = request.app.state.segment_graph

    async def event_stream():
        message_id = str(uuid.uuid4())

        yield encoder.encode(
            RunStartedEvent(thread_id=thread_id, run_id=run_id)
        )
        yield encoder.encode(
            StepStartedEvent(step_name="generate_segment")
        )

        try:
            result = await segment_graph.ainvoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "segment": None,
                    "error": None,
                }
            )

            if result.get("error"):
                yield encoder.encode(
                    RunErrorEvent(message=result["error"])
                )
                return

            segment = result["segment"]

            yield encoder.encode(
                StateSnapshotEvent(snapshot=segment.model_dump())
            )

            yield encoder.encode(
                TextMessageStartEvent(
                    message_id=message_id, role="assistant"
                )
            )
            yield encoder.encode(
                TextMessageContentEvent(
                    message_id=message_id,
                    delta=f"Created segment: **{segment.name}**\n\n{segment.description}",
                )
            )
            yield encoder.encode(
                TextMessageEndEvent(message_id=message_id)
            )

        except Exception as e:
            logging.exception("Segment generation failed")
            yield encoder.encode(RunErrorEvent(message=str(e)))
            return

        yield encoder.encode(
            StepFinishedEvent(step_name="generate_segment")
        )
        yield encoder.encode(
            RunFinishedEvent(thread_id=thread_id, run_id=run_id)
        )

    return StreamingResponse(
        event_stream(), media_type=encoder.get_content_type()
    )


@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    thread_id = _get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = _get_field(body, "run_id", "runId", str(uuid.uuid4()))
    user_message = _extract_user_query(body.get("messages", []))

    chat_agent = request.app.state.chat_agent

    async def event_stream():
        message_id = str(uuid.uuid4())
        message_started = False

        yield encoder.encode(
            RunStartedEvent(thread_id=thread_id, run_id=run_id)
        )

        try:
            async for event in chat_agent.astream_events(
                {"messages": [{"role": "user", "content": user_message}]},
                config={"configurable": {"thread_id": thread_id}},
                version="v2",
            ):
                if (
                    event["event"] == "on_chat_model_stream"
                    and event["data"]["chunk"].content
                ):
                    content = event["data"]["chunk"].content

                    text = ""
                    if isinstance(content, list):
                        for block in content:
                            if (
                                isinstance(block, dict)
                                and block.get("type") == "text"
                            ):
                                text = block["text"]
                                break
                    elif isinstance(content, str):
                        text = content

                    if not text:
                        continue

                    if not message_started:
                        yield encoder.encode(
                            TextMessageStartEvent(
                                message_id=message_id, role="assistant"
                            )
                        )
                        message_started = True

                    yield encoder.encode(
                        TextMessageContentEvent(
                            message_id=message_id, delta=text
                        )
                    )

            if message_started:
                yield encoder.encode(
                    TextMessageEndEvent(message_id=message_id)
                )

        except Exception as e:
            logging.exception("Chat agent error")
            yield encoder.encode(RunErrorEvent(message=str(e)))
            return

        yield encoder.encode(
            RunFinishedEvent(thread_id=thread_id, run_id=run_id)
        )

    return StreamingResponse(
        event_stream(), media_type=encoder.get_content_type()
    )
