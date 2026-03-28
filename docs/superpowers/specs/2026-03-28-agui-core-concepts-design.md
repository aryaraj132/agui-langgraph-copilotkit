# AG-UI Core Concepts Implementation — Design Spec

## Context

This project is a reference implementation demonstrating AG-UI protocol concepts using a Python/FastAPI backend with LangGraph agents and a Next.js/CopilotKit frontend. The domain is an **email marketing platform AI assistant** covering segment generation, template creation, campaign building, custom property generation, and a general-purpose chat orchestrator.

Currently implemented: Segment Generator (state snapshots, lifecycle events, text streaming) and a basic Chat agent (text streaming only). The goal is to implement **all 11 AG-UI core concepts** with proper documentation.

---

## Architecture: Agent-per-Module

Each agent is a self-contained folder with its own routes, graph, state, and README. Routers are registered in `main.py`.

### Agent ↔ Concept Mapping

| Agent | Depth | Primary AG-UI Concepts |
|-------|-------|----------------------|
| **Segment Generator** (extend existing) | Full | Events (lifecycle, text), State Snapshots, Messages, Serialization |
| **Template Creator** (new) | Full | State Deltas (JSON Patch), Tools (FE-defined), Activity Events, Reasoning, Human-in-the-loop |
| **All-Purpose Chat** (extend existing) | Full | Middleware, Capabilities, Tools (BE-defined), Messages (all types), Multi-agent orchestration |
| **Campaign Builder** (new) | Stub | Multi-agent state composition |
| **Custom Properties Generator** (new) | Stub | Custom Events, Generative UI concepts |

---

## Backend Structure

```
src/agui_backend_demo/
├── main.py                          # FastAPI app, registers all routers
├── core/
│   ├── history.py                   # ThreadStore: in-memory dict for conversation history
│   ├── events.py                    # Shared event emission helpers
│   └── middleware.py                # AG-UI middleware implementations
├── agent/
│   ├── segment/
│   │   ├── __init__.py
│   │   ├── routes.py                # APIRouter: POST /api/v1/segment
│   │   ├── graph.py                 # LangGraph StateGraph (existing, refactored)
│   │   ├── state.py                 # SegmentAgentState (existing, refactored)
│   │   └── README.md
│   ├── template/
│   │   ├── __init__.py
│   │   ├── routes.py                # APIRouter: POST /api/v1/template
│   │   ├── graph.py                 # LangGraph with human-in-the-loop
│   │   ├── state.py                 # TemplateAgentState (bidirectional)
│   │   ├── tools.py                 # Frontend-defined tool handling
│   │   └── README.md
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── routes.py                # APIRouter: POST /api/v1/chat
│   │   ├── graph.py                 # ReAct agent with tools (existing, refactored)
│   │   ├── tools.py                 # Backend tools (calls other agents)
│   │   └── README.md
│   ├── campaign/
│   │   ├── __init__.py
│   │   ├── routes.py                # APIRouter: POST /api/v1/campaign
│   │   ├── graph.py                 # Combines segment + template
│   │   ├── state.py                 # CampaignState
│   │   └── README.md
│   └── custom_property/
│       ├── __init__.py
│       ├── routes.py                # APIRouter: POST /api/v1/custom-property
│       ├── graph.py                 # Code generation agent
│       ├── state.py                 # CustomPropertyState
│       └── README.md
├── schemas/
│   ├── segment.py                   # (existing)
│   ├── template.py                  # EmailTemplate schema
│   ├── campaign.py                  # Campaign schema
│   └── custom_property.py           # CustomProperty schema
```

## Frontend Structure

```
frontend/
├── app/
│   ├── layout.tsx                   # Root layout with CopilotKit styles
│   ├── page.tsx                     # Home page with links to all agents
│   ├── chat/page.tsx                # All-purpose chat (extended)
│   ├── segment/page.tsx             # Segment builder (extended)
│   ├── template/page.tsx            # Template creator (split-pane)
│   ├── campaign/page.tsx            # Campaign builder (lighter)
│   ├── custom-property/page.tsx     # Custom property generator (lighter)
│   ├── thread/[threadId]/page.tsx   # Thread viewer (URL-based thread access)
│   └── api/copilotkit/
│       ├── chat/route.ts
│       ├── segment/route.ts
│       ├── template/route.ts
│       ├── campaign/route.ts
│       └── custom-property/route.ts
├── components/
│   ├── Nav.tsx                      # Updated with all agent links
│   ├── SegmentCard.tsx              # (existing)
│   ├── TemplateEditor.tsx           # Split-pane template editor (editable)
│   ├── TemplatePreview.tsx          # HTML email preview (iframe)
│   ├── CampaignBuilder.tsx          # Campaign composition UI
│   ├── CustomPropertyCard.tsx       # Property + code display
│   ├── ActivityIndicator.tsx        # Activity events display
│   ├── ReasoningPanel.tsx           # Chain-of-thought display
│   └── ThreadHistory.tsx            # Conversation history sidebar
├── hooks/
│   ├── useThreadHistory.ts          # Fetch/manage thread history from backend
│   └── useActivityEvents.ts         # Handle activity event rendering
├── lib/
│   └── types.ts                     # Shared TypeScript types
```

---

## Concept Implementations

### 1. Events (Extended)

**Already implemented**: `RUN_STARTED`, `RUN_FINISHED`, `RUN_ERROR`, `STEP_STARTED`, `STEP_FINISHED`, `TEXT_MESSAGE_START/CONTENT/END`, `STATE_SNAPSHOT`

**New events**:
- `STATE_DELTA` — Template Creator uses JSON Patch for incremental updates
- `TOOL_CALL_START/ARGS/END` — Chat agent (BE tools), Template Creator (FE tools)
- `TOOL_CALL_RESULT` — Result of tool execution
- `ACTIVITY_SNAPSHOT` — Template Creator progress indicators
- `REASONING_START/CONTENT/END` — Template Creator chain-of-thought
- `CUSTOM` — Custom Property Generator metadata events
- `MESSAGES_SNAPSHOT` — History restoration on reconnect

### 2. State Management (Bidirectional)

**Template Creator state**:
```python
class TemplateState(TypedDict):
    html: str                    # Full HTML content
    css: str                     # Inline/embedded CSS
    subject: str                 # Email subject line
    preview_text: str            # Email preview text
    sections: list[dict]         # [{id, type, content, styles}]
    version: int                 # For conflict detection
```

- Initial generation → `STATE_SNAPSHOT` with full template
- Subsequent modifications → `STATE_DELTA` with JSON Patch ops
- Human edits on frontend → sent back to backend as updated state in next `RunAgentInput`
- Backend reads frontend state, applies AI changes, emits deltas

### 3. Tools

**Frontend-defined tools (Template Creator)**:
```python
# Agent emits TOOL_CALL_START/ARGS/END for these
# Frontend executes via useCopilotAction
tools = [
    {"name": "update_section", "description": "Update a template section", "parameters": {...}},
    {"name": "add_section", "description": "Add a new template section", "parameters": {...}},
    {"name": "remove_section", "description": "Remove a template section", "parameters": {...}},
]
```

**Backend-defined tools (Chat Agent)**:
```python
# LangGraph tools executed server-side
@tool
def generate_segment(description: str) -> dict:
    """Call the segment generator agent"""

@tool
def create_template(brief: str) -> dict:
    """Call the template creator agent"""

@tool
def build_campaign(segment_id: str, template_id: str, ...) -> dict:
    """Call the campaign builder agent"""
```

### 4. Middleware

Implemented in `core/middleware.py`:
```python
class LoggingMiddleware:
    """Logs all events with timestamps for debugging"""

class CapabilityFilterMiddleware:
    """Filters events based on client-requested capabilities"""

class HistoryMiddleware:
    """Saves all events to ThreadStore for serialization"""
```

Applied to chat agent route as demonstration.

### 5. Capabilities

Each agent declares capabilities via a `GET /api/v1/{agent}/capabilities` endpoint:
```python
SEGMENT_CAPABILITIES = {
    "streaming": True, "state": True, "tools": False, "reasoning": False
}
TEMPLATE_CAPABILITIES = {
    "streaming": True, "state": True, "tools": True, "reasoning": True,
    "human_in_loop": True, "activity": True
}
CHAT_CAPABILITIES = {
    "streaming": True, "state": False, "tools": True, "reasoning": False,
    "multi_agent": True
}
```

### 6. Activity Events

Template Creator emits activity events during processing:
```python
# ActivitySnapshot event
{"type": "ACTIVITY_SNAPSHOT", "messageId": "...", "activityType": "processing",
 "content": {"title": "Analyzing template", "progress": 0.3, "details": "Examining layout structure..."}}
```

Frontend renders via `ActivityIndicator` component.

### 7. Reasoning

Template Creator streams chain-of-thought:
```python
# Event sequence
REASONING_START → REASONING_MESSAGE_START → REASONING_MESSAGE_CONTENT (×N) → REASONING_MESSAGE_END → REASONING_END
```

Frontend displays in collapsible `ReasoningPanel`.

### 8. Messages

All message types demonstrated:
- **User Messages**: Standard user input
- **Assistant Messages**: AI responses, optionally with tool calls
- **System Messages**: Agent instructions (backend only)
- **Tool Messages**: Tool execution results
- **Activity Messages**: Progress indicators (frontend only, never sent to models)
- **Reasoning Messages**: Chain-of-thought (collapsible in UI)

### 9. Serialization & History

**ThreadStore** (`core/history.py`):
```python
thread_store: dict[str, ThreadData] = {}

class ThreadData(TypedDict):
    messages: list[dict]      # All messages in conversation
    events: list[dict]        # All events emitted
    state: dict               # Latest agent state
    agent_type: str           # Which agent
    created_at: str           # ISO timestamp
    updated_at: str           # ISO timestamp
```

**API endpoints**:
- `GET /api/v1/threads` — list all threads with metadata
- `GET /api/v1/threads/{id}` — get thread with full history
- `GET /api/v1/threads/{id}/messages` — messages only

**Frontend integration**:
- URL routing: `/thread/{threadId}` loads specific thread
- On mount, fetches history from backend
- CopilotKit hydrated with existing messages

### 10. Generative UI

Custom Property Generator demonstrates the concept:
- Agent generates both a property definition AND a JavaScript code snippet
- Custom event includes metadata for rendering a code editor component
- Frontend renders live code preview

### 11. Agents

All agents extend the AG-UI agent pattern:
- Implement `run(input: RunAgentInput) → SSE stream`
- Emit standardized event sequences
- Chat agent demonstrates multi-agent orchestration (calls other agents as tools)

---

## Answering Plan Questions

### Q1: FE Tool Call vs BE Tool Call
- **FE Tool Call**: Agent emits `TOOL_CALL_START/ARGS/END` events. Frontend intercepts, executes the tool via `useCopilotAction`, and returns `TOOL_CALL_RESULT`. The backend never executes the tool — it just requests it. Example: Template Creator's `update_section`.
- **BE Tool Call**: Agent calls a LangGraph `@tool` function server-side. Frontend may see `TOOL_CALL_START/END` events for transparency but doesn't execute anything. Example: Chat agent's `generate_segment`.

### Q2: History Management
- All messages stored in backend ThreadStore (Python dict by thread_id)
- Frontend fetches full history via `GET /api/v1/threads/{id}/messages` on page load
- During a run: real-time SSE streaming (incremental events)
- Between runs: full message fetch from backend (no delta — complete history)
- On reconnect/reload: `MESSAGES_SNAPSHOT` event or REST fetch restores state

### Q3: Activity Events (Mocked)
Template Creator emits mock activity events:
- "Analyzing template structure..." (0-20%)
- "Generating section content..." (20-60%)
- "Applying responsive styles..." (60-90%)
- "Finalizing template..." (90-100%)
Displayed via `ActivityIndicator` component with progress bar.

### Q4: Activity Event vs Reasoning
- **Activity Event**: WHAT the agent is doing. User-facing status updates. Brief, action-oriented. Rendered as progress indicators. Never contains internal logic. Example: "Generating header section..."
- **Reasoning Event**: WHY/HOW the agent is thinking. Chain-of-thought showing internal reasoning. Can be lengthy and detailed. Rendered in collapsible panel. May be encrypted for privacy. Example: "The user wants a newsletter. Single-column layouts work best for newsletters because they render reliably across email clients. I'll use a 600px width container with..."

---

## Restrictions Compliance

1. **No FE LLM calls**: All LLM calls happen in Python backend. Frontend only renders and executes FE-defined tools.
2. **Backend history**: ThreadStore saves all messages. Frontend fetches from `/api/v1/threads/*`.
3. **Thread persistence via URL**: `/thread/{threadId}` route in frontend. ThreadStore keyed by threadId. Survives browser close (data in backend memory, lost only on server restart).
