# Segment Generator Agent

## AG-UI Concepts Demonstrated

### Events (Lifecycle & Text Streaming)
- `RUN_STARTED` / `RUN_FINISHED` — brackets every agent run
- `STEP_STARTED` / `STEP_FINISHED` — wraps the `generate_segment` graph node
- `TEXT_MESSAGE_START` / `TEXT_MESSAGE_CONTENT` / `TEXT_MESSAGE_END` — streams the summary text

### State Snapshots
- `STATE_SNAPSHOT` — emits the complete `Segment` Pydantic model as JSON after generation
- Frontend receives via `useCoAgent<Segment>()` hook

### Messages
- User messages contain the audience description
- Assistant messages contain the generated segment summary
- All messages stored in ThreadStore for persistence

### Serialization
- All events stored in ThreadStore via HistoryMiddleware
- Thread history retrievable via `GET /api/v1/threads/{id}`
- Messages retrievable via `GET /api/v1/threads/{id}/messages`

## Event Flow
```
RUN_STARTED → STEP_STARTED("generate_segment") → STATE_SNAPSHOT → TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT → TEXT_MESSAGE_END → STEP_FINISHED → RUN_FINISHED
```

## Files
- `graph.py` — LangGraph StateGraph with structured output via `llm.with_structured_output(Segment)`
- `state.py` — `SegmentAgentState` TypedDict
- `routes.py` — FastAPI APIRouter with SSE streaming
