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


@router.post("/campaign")
async def handle_campaign(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    query = extract_user_query(body.get("messages", []))

    campaign_graph = request.app.state.campaign_graph
    thread = thread_store.get_or_create_thread(thread_id, "campaign")
    prior_messages = list(thread["messages"])
    thread_store.add_message(thread_id, {"role": "user", "content": query})

    async def event_stream():
        message_id = str(uuid.uuid4())
        yield emitter.emit_run_started(thread_id, run_id)

        if prior_messages:
            yield emitter.emit_messages_snapshot(prior_messages)

        yield emitter.emit_step_start("generate_campaign")
        try:
            result = await campaign_graph.ainvoke(
                {
                    "messages": [HumanMessage(content=query)],
                    "campaign": None,
                    "segment": None,
                    "template": None,
                    "error": None,
                }
            )
            if result.get("error"):
                yield emitter.emit_run_error(result["error"])
                return

            campaign = result["campaign"]
            thread_store.update_state(thread_id, {"campaign": campaign})
            yield emitter.emit_state_snapshot(campaign)

            summary = (
                f"Created campaign: **{campaign.get('name', 'Untitled')}**\n\n"
                f"Status: {campaign.get('status', 'draft')}"
            )
            yield emitter.emit_text_start(message_id, "assistant")
            yield emitter.emit_text_content(message_id, summary)
            yield emitter.emit_text_end(message_id)
            thread_store.add_message(
                thread_id, {"role": "assistant", "content": summary}
            )
        except Exception as e:
            logging.exception("Campaign generation failed")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_step_finish("generate_campaign")
        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    stream = LoggingMiddleware().apply(
        HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
    )
    return StreamingResponse(stream, media_type=emitter.content_type)
