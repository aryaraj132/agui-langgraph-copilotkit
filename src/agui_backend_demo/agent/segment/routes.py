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


@router.post("/segment")
async def generate_segment(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    query = extract_user_query(body.get("messages", []))

    segment_graph = request.app.state.segment_graph

    thread = thread_store.get_or_create_thread(thread_id, "segment")
    prior_messages = list(thread["messages"])
    thread_store.add_message(thread_id, {"role": "user", "content": query})

    async def event_stream():
        message_id = str(uuid.uuid4())

        yield emitter.emit_run_started(thread_id, run_id)

        if prior_messages:
            yield emitter.emit_messages_snapshot(prior_messages)

        yield emitter.emit_step_start("generate_segment")

        try:
            result = await segment_graph.ainvoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "segment": None,
                    "error": None,
                }
            )

            if result.get("error"):
                yield emitter.emit_run_error(result["error"])
                return

            segment = result["segment"]
            segment_dict = segment.model_dump()

            thread_store.update_state(thread_id, segment_dict)

            yield emitter.emit_state_snapshot(segment_dict)

            summary = f"Created segment: **{segment.name}**\n\n{segment.description}"
            yield emitter.emit_text_start(message_id, "assistant")
            yield emitter.emit_text_content(message_id, summary)
            yield emitter.emit_text_end(message_id)

            thread_store.add_message(
                thread_id, {"role": "assistant", "content": summary}
            )

        except Exception as e:
            logging.exception("Segment generation failed")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_step_finish("generate_segment")
        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    stream = LoggingMiddleware().apply(
        HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
    )

    return StreamingResponse(stream, media_type=emitter.content_type)
