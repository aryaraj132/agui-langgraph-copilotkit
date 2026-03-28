import json
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from agui_backend_demo.core.events import EventEmitter, extract_user_query, get_field
from agui_backend_demo.core.history import thread_store
from agui_backend_demo.core.middleware import (
    CapabilityFilterMiddleware,
    HistoryMiddleware,
    LoggingMiddleware,
)

router = APIRouter(prefix="/api/v1")
emitter = EventEmitter()


@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    user_message = extract_user_query(body.get("messages", []))

    chat_agent = request.app.state.chat_agent
    thread = thread_store.get_or_create_thread(thread_id, "chat")
    prior_messages = list(thread["messages"])
    thread_store.add_message(thread_id, {"role": "user", "content": user_message})

    async def event_stream():
        message_id = str(uuid.uuid4())
        message_started = False
        full_response = ""
        active_tool_calls: dict[str, str] = {}

        yield emitter.emit_run_started(thread_id, run_id)

        if prior_messages:
            yield emitter.emit_messages_snapshot(prior_messages)

        try:
            async for event in chat_agent.astream_events(
                {"messages": [{"role": "user", "content": user_message}]},
                config={"configurable": {"thread_id": thread_id}},
                version="v2",
            ):
                event_name = event.get("event", "")

                # Handle tool call events (backend tools)
                if event_name == "on_tool_start":
                    tool_call_id = str(uuid.uuid4())
                    tool_name = event.get("name", "unknown")
                    active_tool_calls[event.get("run_id", "")] = tool_call_id
                    yield emitter.emit_tool_call_start(
                        tool_call_id, tool_name, message_id
                    )
                    tool_input = event.get("data", {}).get("input", "")
                    if isinstance(tool_input, dict):
                        yield emitter.emit_tool_call_args(
                            tool_call_id, json.dumps(tool_input)
                        )
                    elif isinstance(tool_input, str):
                        yield emitter.emit_tool_call_args(tool_call_id, tool_input)

                elif event_name == "on_tool_end":
                    run_id_key = event.get("run_id", "")
                    tool_call_id = active_tool_calls.pop(run_id_key, None)
                    if tool_call_id:
                        yield emitter.emit_tool_call_end(tool_call_id)

                # Handle text streaming
                elif (
                    event_name == "on_chat_model_stream"
                    and event["data"]["chunk"].content
                ):
                    content = event["data"]["chunk"].content
                    text = ""
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block["text"]
                                break
                    elif isinstance(content, str):
                        text = content

                    if not text:
                        continue

                    if not message_started:
                        yield emitter.emit_text_start(message_id, "assistant")
                        message_started = True

                    yield emitter.emit_text_content(message_id, text)
                    full_response += text

            if message_started:
                yield emitter.emit_text_end(message_id)
                thread_store.add_message(
                    thread_id, {"role": "assistant", "content": full_response}
                )

        except Exception as e:
            logging.exception("Chat agent error")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    # Apply middleware chain: logging -> capability filter -> history
    stream = LoggingMiddleware().apply(
        CapabilityFilterMiddleware(
            allowed_types={
                "TEXT_MESSAGE_START",
                "TEXT_MESSAGE_CONTENT",
                "TEXT_MESSAGE_END",
                "TOOL_CALL_START",
                "TOOL_CALL_ARGS",
                "TOOL_CALL_END",
                "STATE_SNAPSHOT",
                "STATE_DELTA",
                "MESSAGES_SNAPSHOT",
            }
        ).apply(
            HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
        )
    )
    return StreamingResponse(stream, media_type=emitter.content_type)
