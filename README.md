# AG-UI Demo — LangGraph + CopilotKit

A full-stack demo of the [AG-UI protocol](https://docs.ag-ui.com): a Python FastAPI backend running two LangGraph agents (chat and segment generation), paired with a Next.js + CopilotKit frontend that renders structured agent state as React components — live, inside the chat window and outside it simultaneously.

**The core idea:** zero AI code on the frontend. Every LLM call, every token, every structured output comes from the Python backend. The frontend is a pure renderer.

---

## What This Demonstrates

- **AG-UI protocol** — standardized SSE event streaming between an AI agent backend and any frontend
- **Structured state as UI** — the segment agent emits a `STATE_SNAPSHOT` event with a typed `Segment` object; CopilotKit surfaces this as a live React card rendered directly inside the chat thread (`useCoAgentStateRender`) and in the main page area (`useCoAgent`)
- **Token-level streaming** — the chat agent streams tokens via `astream_events` so text appears word-by-word in real time
- **LangGraph structured output** — Claude returns a validated `Segment` Pydantic model via `with_structured_output`, not free-form text
- **Conversation memory** — the chat agent persists message history per `thread_id` via LangGraph's checkpointer

---

## Architecture

```
Browser (Next.js + CopilotKit)
  │
  │  POST /api/copilotkit/*  (CopilotKit wire format)
  ▼
Next.js API Routes  ← CopilotRuntime + LangGraphHttpAgent
  │
  │  POST /api/v1/*  (AG-UI RunAgentInput)
  ▼
Python FastAPI Backend
  │
  ├── /api/v1/chat     → create_react_agent → Claude → token stream
  └── /api/v1/segment  → LangGraph StateGraph → Claude (structured output) → Segment
  │
  │  SSE: AG-UI events (RUN_STARTED, STATE_SNAPSHOT, TEXT_MESSAGE_CONTENT, ...)
  ▼
CopilotKit parses events →
  ├── useCoAgentStateRender → <SegmentCard> rendered inside the chat thread
  └── useCoAgent            → <SegmentCard> rendered in the main page area
```

---

## Prerequisites

- [mise](https://mise.jdx.dev/) — installs Python 3.13, uv, and just automatically
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

```bash
# Install all tools (Python, uv, just) via mise
mise install

# Install backend + frontend dependencies
just prepare
```

---

## Running

```bash
# Terminal 1 — Python backend on http://localhost:8000
export ANTHROPIC_API_KEY=sk-ant-...
just backend

# Terminal 2 — Next.js frontend on http://localhost:3000
just frontend
```

Open `http://localhost:3000`. Navigate to:
- `/chat` — general-purpose chat agent with streaming text
- `/segment` — describe an audience ("US users who purchased in the last 30 days") and watch a structured segment card appear inside the chat and in the main page area simultaneously

---

## Backend Endpoints

| Method | Path | Agent | Description |
|--------|------|-------|-------------|
| `GET` | `/health` | — | Health check → `{"status": "ok"}` |
| `POST` | `/api/v1/chat` | ReAct chat agent | Streams tokens via SSE, maintains conversation history per `thread_id` |
| `POST` | `/api/v1/segment` | LangGraph segment graph | Emits `STATE_SNAPSHOT` (structured `Segment` object) + text summary |

Both agent endpoints accept an AG-UI `RunAgentInput` body and stream AG-UI protocol events over SSE.

### Request Format

```json
{
  "thread_id": "unique-thread-id",
  "run_id": "unique-run-id",
  "messages": [
    { "id": "msg-1", "role": "user", "content": "Active US users who made a purchase" }
  ]
}
```

### Segment Agent — Event Flow

```
RUN_STARTED → STEP_STARTED → STATE_SNAPSHOT → TEXT_MESSAGE_START →
TEXT_MESSAGE_CONTENT → TEXT_MESSAGE_END → STEP_FINISHED → RUN_FINISHED
```

`STATE_SNAPSHOT` carries the fully structured segment:

```json
{
  "type": "STATE_SNAPSHOT",
  "snapshot": {
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

### Chat Agent — Event Flow

```
RUN_STARTED → TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT (×N tokens) →
TEXT_MESSAGE_END → RUN_FINISHED
```

### Test with curl

```bash
# Segment agent
curl -N -X POST http://localhost:8000/api/v1/segment \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"t1","run_id":"r1","messages":[{"id":"m1","role":"user","content":"Active users from the US who made a purchase"}]}'

# Chat agent
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"t2","run_id":"r2","messages":[{"id":"m1","role":"user","content":"What is LangGraph?"}]}'
```

---

## Project Structure

```
├── src/agui_backend_demo/
│   ├── main.py              # FastAPI app, lifespan (agent init), CORS
│   ├── api/routes.py        # AG-UI SSE endpoints (/segment, /chat)
│   ├── agent/
│   │   ├── graph.py         # LangGraph StateGraph — segment generation
│   │   ├── chat_agent.py    # create_react_agent — general chat
│   │   └── state.py         # SegmentAgentState TypedDict
│   └── schemas/segment.py   # Pydantic: Segment, ConditionGroup, Condition
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx           # Root layout — imports CopilotKit styles
│   │   ├── page.tsx             # Home — links to /chat and /segment
│   │   ├── chat/page.tsx        # CopilotKit sidebar + chat agent
│   │   ├── segment/page.tsx     # CopilotKit sidebar + useCoAgent + useCoAgentStateRender
│   │   └── api/copilotkit/
│   │       ├── chat/route.ts    # CopilotRuntime → /api/v1/chat
│   │       └── segment/route.ts # CopilotRuntime → /api/v1/segment
│   └── components/
│       ├── Nav.tsx              # Top nav bar
│       └── SegmentCard.tsx      # Styled segment display (pure component)
│
├── tests/
│   └── test_schemas.py      # Pydantic schema validation tests
│
├── justfile                 # Dev commands
├── pyproject.toml           # Python deps + build config
└── CopilotKit-Helpspace.md  # Full technical reference (read this)
```

---

## Key CopilotKit Patterns

**`useCoAgentStateRender`** — renders a React component inside the chat thread at the point where the agent responded. When the segment agent emits `STATE_SNAPSHOT`, this hook injects `<SegmentCard>` directly into the message slot.

**`useCoAgent`** — subscribes to agent state as a React value. Drives the `<SegmentCard>` rendered in the main page area outside the chat. Updates live on every `STATE_SNAPSHOT`.

Both hooks read from the same event stream. The distinction: `useCoAgentStateRender` controls placement (inside chat, per-run), `useCoAgent` gives you the value (anywhere, always latest).

---

## Development

```bash
just test         # Run pytest
just check        # Lint + format check (ruff)
just fix          # Auto-fix lint + formatting
just prepare      # Install all deps (backend + frontend)
```

---

## Tech Stack

**Backend**
- [AG-UI Protocol](https://docs.ag-ui.com) — standardized agent-UI communication over SSE
- [LangGraph](https://langchain-ai.github.io/langgraph/) — agent graph orchestration
- [langchain-anthropic](https://python.langchain.com/docs/integrations/providers/anthropic/) — Claude API with structured output
- [FastAPI](https://fastapi.tiangolo.com/) — async HTTP server
- [Pydantic v2](https://docs.pydantic.dev/) — schema validation
- [uv](https://docs.astral.sh/uv/) — Python package management
- [mise](https://mise.jdx.dev/) — tool version management
- [just](https://just.systems/) — command runner

**Frontend**
- [CopilotKit](https://docs.copilotkit.ai) — AG-UI hooks and chat UI components
- [Next.js 15](https://nextjs.org/) — React framework with App Router
- [Tailwind CSS v4](https://tailwindcss.com/) — utility-first styling
- [Playground](https://feature-viewer.copilotkit.ai/langgraph/feature/agentic_chat?file=page.tsx)

---

## Further Reading

See [`CopilotKit-Helpspace.md`](./CopilotKit-Helpspace.md) for a complete technical walkthrough — every hook, every event type, every connection in the stack explained in full detail.
