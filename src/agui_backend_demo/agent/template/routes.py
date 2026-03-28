import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from agui_backend_demo.core.events import EventEmitter, extract_user_query, get_field
from agui_backend_demo.core.history import thread_store
from agui_backend_demo.core.middleware import HistoryMiddleware, LoggingMiddleware

router = APIRouter(prefix="/api/v1")
emitter = EventEmitter()

REASONING_STEPS = [
    "Analyzing the user's request for an email template...",
    "Considering email client compatibility requirements...",
    "Planning section layout: header, body, CTA, footer...",
    "Selecting responsive design approach with 600px container...",
]


def _compute_json_patch(old: dict, new: dict) -> list[dict]:
    """Compute a simple JSON Patch (RFC 6902) between two flat dicts."""
    ops: list[dict] = []
    all_keys = set(list(old.keys()) + list(new.keys()))
    for key in sorted(all_keys):
        path = f"/{key}"
        if key not in old:
            ops.append({"op": "add", "path": path, "value": new[key]})
        elif key not in new:
            ops.append({"op": "remove", "path": path})
        elif old[key] != new[key]:
            ops.append({"op": "replace", "path": path, "value": new[key]})
    return ops


def _try_parse_partial_json(s: str) -> dict | None:
    """Try to parse a partial JSON string by adding closing brackets."""
    s = s.strip()
    if not s:
        return None
    for suffix in ["", "}", '"}',"\"}", "]}", "\"]}",  '"]}',"\"]}}"]:
        try:
            result = json.loads(s + suffix)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            continue
    return None


@router.post("/template")
async def handle_template(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    query = extract_user_query(body.get("messages", []))
    frontend_state = body.get("state")

    template_graph = request.app.state.template_graph

    thread = thread_store.get_or_create_thread(thread_id, "template")
    thread_store.add_message(thread_id, {"role": "user", "content": query})
    snapshot_messages = list(thread["messages"])

    existing_template = frontend_state or thread["state"].get("template")

    async def event_stream():
        message_id = str(uuid.uuid4())
        reasoning_id = str(uuid.uuid4())
        activity_id = str(uuid.uuid4())

        yield emitter.emit_run_started(thread_id, run_id)

        if len(snapshot_messages) > 1:
            yield emitter.emit_messages_snapshot(snapshot_messages)

        yield emitter.emit_step_start("template_processing")

        # --- REASONING EVENTS ---
        yield emitter.emit_reasoning_start(reasoning_id)
        yield emitter.emit_reasoning_message_start(reasoning_id)
        for step in REASONING_STEPS:
            yield emitter.emit_reasoning_content(reasoning_id, step + " ")
            await asyncio.sleep(0.1)
        yield emitter.emit_reasoning_message_end(reasoning_id)
        yield emitter.emit_reasoning_end(reasoning_id)

        try:
            graph_input = {
                "messages": [HumanMessage(content=query)],
                "template": existing_template,
                "error": None,
                "version": (
                    existing_template.get("version", 0) if existing_template else 0
                ),
            }

            # --- REAL-TIME STREAMING ---
            # Use astream_events to capture partial structured output
            # and emit progressive state updates as the LLM generates.
            accumulated_json = ""
            last_emitted_keys: set[str] = set()
            new_template = None
            graph_error = None
            chunk_count = 0

            # Activity: show generation starting
            yield emitter.emit_activity_snapshot(
                activity_id, "processing",
                {"title": "Generating template", "progress": 0.1, "details": "Starting LLM generation..."},
            )

            async for event in template_graph.astream_events(
                graph_input, version="v2"
            ):
                event_name = event.get("event", "")

                if event_name == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]

                    # Structured output streams as tool call chunks
                    if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                        for tc_chunk in chunk.tool_call_chunks:
                            args = tc_chunk.get("args", "")
                            if args:
                                accumulated_json += args
                                chunk_count += 1

                                # Try parsing partial JSON every few chunks.
                                # Emit STATE_DELTA (JSON Patch) for new fields
                                # so the frontend merges them into existing
                                # state instead of replacing it.
                                if chunk_count % 5 == 0:
                                    partial = _try_parse_partial_json(accumulated_json)
                                    if partial:
                                        new_keys = set(partial.keys())
                                        newly_added = new_keys - last_emitted_keys
                                        if newly_added:
                                            # Build JSON Patch ops for new/changed fields
                                            delta = []
                                            for key in newly_added:
                                                op = "add" if key not in last_emitted_keys else "replace"
                                                delta.append({"op": op, "path": f"/{key}", "value": partial[key]})
                                            yield emitter.emit_state_delta(delta)

                                            # Update activity based on newly appeared fields
                                            if "subject" in newly_added:
                                                yield emitter.emit_activity_snapshot(
                                                    activity_id, "processing",
                                                    {"title": f"Subject: {partial['subject']}", "progress": 0.3, "details": "Generating content..."},
                                                )
                                            if "sections" in partial:
                                                section_count = len(partial.get("sections", []))
                                                progress = min(0.5 + section_count * 0.1, 0.9)
                                                yield emitter.emit_activity_snapshot(
                                                    activity_id, "processing",
                                                    {"title": f"Building sections ({section_count})", "progress": progress, "details": "Adding sections..."},
                                                )

                                            last_emitted_keys = new_keys

                elif event_name == "on_chain_end":
                    # Capture the final graph output
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict) and "template" in output:
                        new_template = output["template"]
                        graph_error = output.get("error")

            if graph_error:
                yield emitter.emit_run_error(graph_error)
                return

            if new_template is None:
                yield emitter.emit_run_error("Template generation produced no result")
                return

            # --- FINAL STATE SNAPSHOT ---
            yield emitter.emit_activity_snapshot(
                activity_id, "processing",
                {"title": "Finalizing template", "progress": 1.0, "details": "Template ready"},
            )

            if existing_template is not None:
                patch = _compute_json_patch(existing_template, new_template)
                if patch:
                    yield emitter.emit_state_delta(patch)

            yield emitter.emit_state_snapshot(new_template)
            thread_store.update_state(thread_id, {"template": new_template})

            # --- TOOL CALL EVENTS (demonstrating FE-defined tools) ---
            sections = new_template.get("sections", [])
            if sections:
                tool_call_id = str(uuid.uuid4())
                yield emitter.emit_tool_call_start(
                    tool_call_id, "update_section", message_id
                )
                yield emitter.emit_tool_call_args(
                    tool_call_id,
                    json.dumps(
                        {
                            "section_id": sections[0].get("id", "s1"),
                            "content": sections[0].get("content", ""),
                        }
                    ),
                )
                yield emitter.emit_tool_call_end(tool_call_id)

            # --- TEXT MESSAGE ---
            action = "Updated" if existing_template else "Created"
            subject = new_template.get("subject", "Untitled")
            section_count = len(sections)
            summary = (
                f"{action} template: **{subject}**\n\n"
                f"{section_count} section(s) generated."
            )
            yield emitter.emit_text_start(message_id, "assistant")
            yield emitter.emit_text_content(message_id, summary)
            yield emitter.emit_text_end(message_id)

            thread_store.add_message(
                thread_id, {"role": "assistant", "content": summary}
            )

        except Exception as e:
            logging.exception("Template generation failed")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_step_finish("template_processing")
        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    stream = LoggingMiddleware().apply(
        HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
    )
    return StreamingResponse(stream, media_type=emitter.content_type)
