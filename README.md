# Segment Generation Agent

A demo backend that uses [LangGraph](https://langchain-ai.github.io/langgraph/) and the Claude API to power AI agents, with [AG-UI protocol](https://docs.ag-ui.com) compliant SSE streaming. Compatible with any AG-UI frontend framework (CopilotKit, Pydantic AI, custom implementations, etc.).

## Prerequisites

- [mise](https://mise.jdx.dev/) (installs Python 3.13, uv, just)
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

```bash
mise install
just install
```

## Usage

```bash
export ANTHROPIC_API_KEY=sk-ant-...
just run
```

The server starts on `http://localhost:8000`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/segment` | Generate a user segment (AG-UI SSE stream) |
| `POST` | `/api/v1/chat` | Generic chat agent (AG-UI SSE stream) |

Both agent endpoints accept an AG-UI `RunAgentInput` body and return AG-UI protocol events over SSE.

## AG-UI Protocol

All agent endpoints follow the [AG-UI event specification](https://docs.ag-ui.com/concepts/events). Events are streamed as `data: {json}\n\n` with camelCase field names.

### Request Format (RunAgentInput)

```json
{
  "thread_id": "unique-thread-id",
  "run_id": "unique-run-id",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Users from the US who signed up in the last 30 days"
    }
  ],
  "tools": [],
  "context": [],
  "state": {}
}
```

### Segment Endpoint

```bash
curl -N -X POST http://localhost:8000/api/v1/segment \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "t1",
    "run_id": "r1",
    "messages": [{"id": "m1", "role": "user", "content": "Active users from the US who made a purchase"}],
    "tools": [], "context": [], "state": {}
  }'
```

**Event flow:**
```
RUN_STARTED → STEP_STARTED → STATE_SNAPSHOT (structured segment) →
TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT → TEXT_MESSAGE_END →
STEP_FINISHED → RUN_FINISHED
```

The `STATE_SNAPSHOT` event contains the structured segment data:

```json
{
  "type": "STATE_SNAPSHOT",
  "state": {
    "name": "Active US Buyers",
    "description": "Users from the US who have made at least one purchase",
    "condition_groups": [
      {
        "logical_operator": "AND",
        "conditions": [
          { "field": "country", "operator": "equals", "value": "US" },
          { "field": "purchase_count", "operator": "greater_than_or_equal", "value": 1 }
        ]
      }
    ],
    "estimated_scope": "Users matching location and purchase criteria"
  }
}
```

### Chat Endpoint

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "t2",
    "run_id": "r2",
    "messages": [{"id": "m1", "role": "user", "content": "What is LangGraph?"}],
    "tools": [], "context": [], "state": {}
  }'
```

**Event flow:**
```
RUN_STARTED → TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT (token)... →
TEXT_MESSAGE_END → RUN_FINISHED
```

Tokens are streamed as they are generated, enabling real-time display.

## Development

```bash
just test       # Run tests
just check      # Lint + format check
just fix        # Auto-fix lint + format
```

## Project Structure

```
src/agui_backend_demo/
  main.py              # FastAPI app with lifespan, CORS, health check
  api/routes.py        # AG-UI protocol endpoints (segment + chat)
  agent/graph.py       # LangGraph StateGraph for segment generation
  agent/chat_agent.py  # create_react_agent for generic chat
  agent/state.py       # Agent state TypedDict
  schemas/segment.py   # Pydantic: Segment, ConditionGroup, Condition
```

## Tech Stack

- **AG-UI Protocol** (`ag-ui-protocol`) — framework-agnostic agent-UI communication
- **LangGraph** — agent workflow orchestration
- **langchain-anthropic** — Claude API integration with structured output
- **FastAPI** — API server with SSE streaming
- **Pydantic** — structured output schema validation
- **uv** — Python package management
- **mise** — tool version management
- **just** — command runner
