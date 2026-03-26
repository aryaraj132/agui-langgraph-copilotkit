# CopilotKit Helpspace

A complete reference for how this project works — every layer, every hook, every protocol detail. Covers what is used, what is not yet used, and why every decision was made.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack & Dev Tooling](#tech-stack--dev-tooling)
3. [Environment & Configuration](#environment--configuration)
4. [AG-UI Protocol — Complete Reference](#ag-ui-protocol--complete-reference)
5. [Backend — Deep Dive](#backend--deep-dive)
6. [Frontend — Deep Dive](#frontend--deep-dive)
7. [CopilotKit UI Components](#copilotkit-ui-components)
8. [CopilotKit Hooks — All of Them](#copilotkit-hooks--all-of-them)
9. [The Inner Component Pattern](#the-inner-component-pattern)
10. [SegmentCard Component](#segmentcard-component)
11. [Full Data Flows](#full-data-flows)
12. [AG-UI Events Not Yet Used](#ag-ui-events-not-yet-used)
13. [Tests](#tests)
14. [How to Extend This Project](#how-to-extend-this-project)

---

## Project Overview

This project is a demonstration of **AG-UI protocol** — a standardized contract for streaming AI agent output to any frontend. It consists of:

- A **Python FastAPI backend** running two LangGraph agents (a chat agent and a segment generation agent), each streaming AG-UI events over SSE
- A **Next.js frontend** using CopilotKit to consume those streams, render a chat sidebar, and surface agent state as React components

The key principle: **zero AI code on the frontend**. Every LLM call, every token, every structured output comes from the Python backend. The frontend only renders what the backend sends.

```
User → CopilotSidebar → Next.js API route → Python FastAPI → Claude → SSE → React
```

---

## Tech Stack & Dev Tooling

### Backend

| Package | Version | Purpose |
|---------|---------|---------|
| `ag-ui-protocol` | >=0.1.14 | AG-UI event types and SSE encoder |
| `langgraph` | >=0.4.1 | Agent graph orchestration |
| `langchain-anthropic` | >=0.4.4 | Claude API integration via LangChain |
| `langchain-core` | >=0.3.59 | Base LangChain abstractions |
| `fastapi` | >=0.115.0 | HTTP server and SSE streaming |
| `uvicorn` | >=0.34.0 | ASGI server that runs FastAPI |
| `pydantic` | >=2.11.0 | Schema validation and structured output |

### Frontend

| Package | Purpose |
|---------|---------|
| `@copilotkit/react-core` | Hooks: `useCoAgent`, `useCoAgentStateRender`, etc. |
| `@copilotkit/react-ui` | UI: `CopilotSidebar`, `CopilotPopup`, `CopilotChat`, `CopilotTextarea` |
| `@copilotkit/runtime` | Server: `CopilotRuntime`, `LangGraphHttpAgent`, `EmptyAdapter` |
| `next` | React framework with App Router |
| `tailwindcss` v4 | Utility-first CSS |

### Dev Tools

**mise** — a polyglot tool version manager (replaces nvm, pyenv, etc.). The `mise.toml` file pins Python 3.13 and other tools so every developer gets identical versions. Run `mise install` once and all tools are available.

**uv** — a fast Python package manager (replaces pip + virtualenv). `uv sync` reads `pyproject.toml` and installs all dependencies into a local `.venv`. `uv run` executes commands inside that environment without needing to activate it.

**just** — a command runner (like `make` but without the historical baggage). The `justfile` defines named recipes:

```
just prepare      # uv sync + npm install (first-time setup)
just backend      # start FastAPI on port 8000
just frontend     # start Next.js on port 3000
just test         # run pytest
just check        # ruff lint + format check
just fix          # ruff lint-fix + format (auto-fixes)
```

**ruff** — an extremely fast Python linter and formatter (replaces flake8 + black). Configured via `pyproject.toml`.

**pytest + pytest-asyncio** — testing framework. `pytest-asyncio` is needed because some test scenarios involve `async` functions.

**hatchling** — the build backend for the Python package. Configured in `pyproject.toml` under `[build-system]`. It tells Python how to package `src/agui_backend_demo` into a distributable wheel.

---

## Environment & Configuration

### Backend

The backend reads `ANTHROPIC_API_KEY` from the environment. This must be set before starting the server:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
just backend
```

If the key is not set, the FastAPI server starts but every agent request will fail when it tries to call Claude.

### Frontend

**File:** `frontend/.env.local`

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**Why `NEXT_PUBLIC_`?** Next.js strips all environment variables from the browser bundle by default for security. The `NEXT_PUBLIC_` prefix is the explicit opt-in to expose a variable to the browser. Without this prefix, the variable would be `undefined` in client-side code.

This variable is used in the Next.js API routes (server-side) to construct the URL that `LangGraphHttpAgent` calls:

```typescript
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
```

### Styling

**File:** `frontend/app/globals.css`

Uses Tailwind v4's new CSS-first configuration: `@import "tailwindcss"` replaces the old `@tailwind base/components/utilities` directives. No `tailwind.config.js` needed — Tailwind v4 scans your source files automatically.

CSS custom properties (`--background`, `--foreground`) are defined here and switch automatically via `prefers-color-scheme` media query for dark mode support.

**File:** `frontend/app/layout.tsx`

```typescript
import "@copilotkit/react-ui/styles.css";
```

CopilotKit's UI styles must be imported in the root layout — not inside individual pages — because the layout is the one file that wraps every page. If you imported it only in the segment page, the chat page sidebar would be unstyled.

---

## AG-UI Protocol — Complete Reference

AG-UI is a standardized event protocol for streaming AI agent output over Server-Sent Events (SSE). It defines a wire format that any agent backend can implement and any frontend can consume.

### Wire Format

Every event is a JSON-encoded line:

```
data: {"type": "EVENT_TYPE", "camelCaseField": "value"}\n\n
```

The double newline `\n\n` is the SSE standard event delimiter. The browser's native `EventSource` API and manual SSE parsers both use this to split events.

Field names in the JSON are **camelCase** — this matters because the Python backend uses snake_case internally. The `ag-ui-protocol` library handles the conversion automatically when serializing events.

### Content Type

The response must have `Content-Type: text/event-stream`. The `EventEncoder` from `ag-ui-protocol` sets this automatically via `encoder.get_content_type()`.

### RunAgentInput — The Request Schema

Every request to an AG-UI endpoint sends this body:

```typescript
interface RunAgentInput {
  thread_id: string;        // Conversation identifier — same across turns in a thread
  run_id: string;           // Unique per request — each send generates a new one
  messages: Message[];      // Full conversation history up to this point
  tools?: Tool[];           // Tools the agent is allowed to use
  context?: Context[];      // Background information the agent should know
  state?: object;           // Agent state to restore (for stateful agents)
  forwarded_props?: object; // Custom key-value config passed through untouched
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string | InputContent[];  // string for text, array for multimodal
}

// Multimodal content (not yet used in this project)
interface InputContent {
  type: "text" | "binary";
  text?: string;         // for type="text"
  mime_type?: string;    // for type="binary" (e.g. "image/png")
  data?: string;         // base64-encoded bytes for type="binary"
}
```

**`thread_id` vs `run_id`:**
- `thread_id` stays constant for the entire conversation. LangGraph uses this to look up conversation history from its checkpointer (memory store), so follow-up questions have context.
- `run_id` is generated fresh for each user message. It uniquely identifies this specific invocation. Used in `RUN_STARTED`/`RUN_FINISHED` events to correlate the start and end of a run.

**`tools`:** An array of tool definitions the agent can call back on the frontend. This enables the agent to invoke frontend actions (e.g., open a modal, navigate to a page). Not used in this project.

**`context`:** A list of `{ description, value }` pairs providing background context the agent should be aware of — things like "the user is on the billing page" or "the user's plan is premium". Not used in this project.

**`state`:** The agent's state at the start of the run. For stateful agents (like the segment agent), you could pass the previous segment back here so the agent can refine it. Not used in this project.

**`forwarded_props`:** An opaque passthrough object. CopilotKit uses this to send its own internal metadata. Your backend receives it and can inspect it for custom routing or configuration.

### All AG-UI Event Types

#### Lifecycle Events

**`RUN_STARTED`** — first event in every stream. Signals the run has begun.
```json
{ "type": "RUN_STARTED", "threadId": "t1", "runId": "r1" }
```

**`RUN_FINISHED`** — last event on success. Signals normal completion.
```json
{ "type": "RUN_FINISHED", "threadId": "t1", "runId": "r1" }
```

**`RUN_ERROR`** — terminal failure event. No `RUN_FINISHED` follows.
```json
{ "type": "RUN_ERROR", "message": "API key not set", "code": "auth_error" }
```

**`STEP_STARTED`** / **`STEP_FINISHED`** — bracket a named node in the agent graph. Used in the segment endpoint to bracket the `generate_segment` node.
```json
{ "type": "STEP_STARTED", "stepName": "generate_segment" }
{ "type": "STEP_FINISHED", "stepName": "generate_segment" }
```

#### Text Streaming Events

**`TEXT_MESSAGE_START`** — announces an incoming text message. The `messageId` links this to its content events.
```json
{ "type": "TEXT_MESSAGE_START", "messageId": "m1", "role": "assistant" }
```

**`TEXT_MESSAGE_CONTENT`** — one chunk of streamed text. The `delta` is the incremental text since the last event.
```json
{ "type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hello" }
```

**`TEXT_MESSAGE_END`** — marks the end of this message's text stream.
```json
{ "type": "TEXT_MESSAGE_END", "messageId": "m1" }
```

#### State Events

**`STATE_SNAPSHOT`** — the complete current state of the agent. Replaces whatever state was known before. Used in this project to send the full `Segment` object.
```json
{ "type": "STATE_SNAPSHOT", "snapshot": { "name": "...", "conditionGroups": [...] } }
```

**`STATE_DELTA`** — an incremental update to the agent state using **JSON Patch** format (RFC 6902). Instead of resending the full state, it sends only what changed. Not used in this project but valuable for large state objects.
```json
{
  "type": "STATE_DELTA",
  "delta": [
    { "op": "replace", "path": "/name", "value": "Updated Segment Name" },
    { "op": "add", "path": "/condition_groups/0/conditions/-", "value": { "field": "age", "operator": "greater_than", "value": 18 } }
  ]
}
```

JSON Patch operations: `add`, `remove`, `replace`, `move`, `copy`, `test`.

#### Tool Call Events

These three events bracket a single tool invocation. They follow the same Start → Content → End streaming pattern as text messages.

**`TOOL_CALL_START`** — the agent wants to call a tool.
```json
{ "type": "TOOL_CALL_START", "toolCallId": "tc1", "toolCallName": "navigate_to_page" }
```

**`TOOL_CALL_ARGS`** — streams the arguments as a JSON string fragment. Multiple events accumulate into the full args JSON.
```json
{ "type": "TOOL_CALL_ARGS", "toolCallId": "tc1", "delta": "{\"page\": \"/dash" }
{ "type": "TOOL_CALL_ARGS", "toolCallId": "tc1", "delta": "board\"}" }
```

**`TOOL_CALL_END`** — arguments are complete, the tool should now execute.
```json
{ "type": "TOOL_CALL_END", "toolCallId": "tc1" }
```

Not used in this project. Requires `useCopilotAction` on the frontend to handle.

#### Message Snapshot Event

**`MESSAGES_SNAPSHOT`** — sends the full conversation history at once. Used for:
- Initial load when restoring a conversation from persistent storage
- Connection recovery after a dropped SSE stream
- State synchronization when multiple clients share a thread

```json
{
  "type": "MESSAGES_SNAPSHOT",
  "messages": [
    { "id": "m1", "role": "user", "content": "Hello" },
    { "id": "m2", "role": "assistant", "content": "Hi there!" }
  ]
}
```

Not used in this project.

#### Special Events

**`CUSTOM`** — an application-defined event for anything outside the standard protocol. The frontend decides how to handle it.
```json
{ "type": "CUSTOM", "name": "segment_score_update", "value": { "score": 0.87 } }
```

**`REASONING`** — exposes the agent's internal chain-of-thought. Used with models that support explicit reasoning (e.g., Claude's extended thinking mode). The content is the model's reasoning text before its final answer.
```json
{ "type": "REASONING", "content": "The user wants active users, so I should use login_count > 0..." }
```

---

## Backend — Deep Dive

### FastAPI App & Lifespan

**File:** `src/agui_backend_demo/main.py`

FastAPI's `lifespan` context manager is the modern replacement for `@app.on_event("startup")`. It runs once when the server starts, and anything after the `yield` runs on shutdown.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.segment_graph = build_segment_graph()
    app.state.chat_agent = build_chat_agent()
    yield
    # shutdown code would go here
```

**Why build agents at startup?** LangGraph compiles the `StateGraph` at `graph.compile()` — this is expensive. If you built the graph per request, every user message would pay that cost. Stored on `app.state`, the compiled graph is shared across all requests for the lifetime of the process.

**`app.state`** is FastAPI's built-in attribute bag — a simple namespace you can attach anything to. It is accessible in route handlers via `request.app.state`.

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_origins=["*"]` allows any origin — needed in development so `localhost:3000` (Next.js) can call `localhost:8000` (FastAPI). Note `allow_credentials=False` — you cannot use `allow_origins=["*"]` together with `allow_credentials=True` (browser security restriction). For production, replace `"*"` with your exact frontend URL and set `allow_credentials=True` if you need cookies.

### Pydantic Schemas

**File:** `src/agui_backend_demo/schemas/segment.py`

```python
class Condition(BaseModel):
    field: str
    operator: str
    value: str | int | float | list[str]   # union type — Claude picks the right one

class ConditionGroup(BaseModel):
    logical_operator: Literal["AND", "OR"]  # enum constraint
    conditions: list[Condition]

class Segment(BaseModel):
    name: str
    description: str
    condition_groups: list[ConditionGroup]
    estimated_scope: str | None = None      # optional field
```

**`Literal["AND", "OR"]`** — Pydantic enforces this at validation time. If Claude returns `"XOR"`, Pydantic raises a `ValidationError` (tested in the test suite). This is also what makes `with_structured_output` reliable — the JSON schema sent to Claude includes the enum constraint.

**`str | int | float | list[str]`** for `value` — conditions can match against string literals (`country = "US"`), numeric thresholds (`age > 18`), decimal amounts (`total_spent > 99.99`), or lists (`country in ["US", "CA", "UK"]`).

**`model_dump()`** — called in the route to convert the `Segment` instance to a plain dict for the `STATE_SNAPSHOT` event. Pydantic v2's `model_dump()` outputs Python-native types; `model_dump_json()` gives a JSON string.

### LangGraph StateGraph — Segment Agent

**File:** `src/agui_backend_demo/agent/graph.py`

```python
graph = StateGraph(SegmentAgentState)
graph.add_node("generate_segment", _build_generate_node(llm))
graph.add_edge(START, "generate_segment")
graph.add_edge("generate_segment", END)
return graph.compile()
```

**`StateGraph(SegmentAgentState)`** — creates a graph whose state schema is `SegmentAgentState`. Every node in the graph receives the full state dict and returns a partial dict of updates. LangGraph merges the partial dict back into the state (it does not replace the entire state — only the keys you return are updated).

**`add_edge(START, ...)`** and **`add_edge(..., END)`** — `START` and `END` are LangGraph sentinels. The graph is a directed graph; edges define execution order. This graph has exactly one path: START → generate_segment → END.

**`graph.compile()`** — validates the graph (no cycles, all edges reference real nodes, etc.) and returns a `CompiledStateGraph` that can be invoked with `.ainvoke()` or `.astream_events()`.

**The generate_segment node:**

```python
structured_llm = llm.with_structured_output(Segment)
result = await structured_llm.ainvoke(messages)
```

`with_structured_output(Segment)` — LangChain generates a JSON schema from the Pydantic `Segment` model and passes it to Claude as a tool definition. Claude is instructed to respond by calling that tool with arguments matching the schema. LangChain receives the tool-call response and deserializes the arguments back into a `Segment` instance. Your code never sees raw JSON — only a typed Python object.

### LangGraph Agent State

**File:** `src/agui_backend_demo/agent/state.py`

```python
class SegmentAgentState(TypedDict):
    messages: list
    segment: Segment | None
    error: str | None
```

`TypedDict` is Python's way of typing dictionaries without creating a class. LangGraph uses this as a schema — it validates that node return dicts only contain keys defined here. If you try to return `{"unknown_key": "value"}` from a node, LangGraph will raise an error.

The route initializes state at invocation time:
```python
result = await segment_graph.ainvoke({
    "messages": [HumanMessage(content=query)],
    "segment": None,
    "error": None,
})
```

After `ainvoke` completes, `result` is the final merged state dict. The route reads `result["segment"]` for the generated `Segment`, or `result["error"]` if something failed.

### Chat Agent — create_react_agent

**File:** `src/agui_backend_demo/agent/chat_agent.py`

```python
return create_react_agent(llm, tools=[], prompt=SYSTEM_PROMPT)
```

`create_react_agent` is a LangGraph prebuilt that creates a **ReAct** (Reason + Act) graph. The full graph structure is:

```
START → agent (calls LLM) → tools (executes tools) → agent (loops) → END
```

When `tools=[]`, the tools node is effectively a no-op and the graph always exits after the first LLM call. The value of using `create_react_agent` even with no tools is:
- Ready to add tools without restructuring
- Built-in conversation memory via LangGraph's checkpointing
- Consistent interface with `astream_events`

**Conversation memory** — when the chat route passes `config={"configurable": {"thread_id": thread_id}}`, LangGraph's in-memory checkpointer stores the message history keyed by `thread_id`. The next request with the same `thread_id` automatically loads that history, so the agent has context from previous turns. This is why the chat agent can answer follow-up questions ("what did I just ask?").

### astream_events — Token-Level Streaming

**File:** `src/agui_backend_demo/api/routes.py` (chat route)

```python
async for event in chat_agent.astream_events(
    {"messages": [{"role": "user", "content": user_message}]},
    config={"configurable": {"thread_id": thread_id}},
    version="v2",
):
    if event["event"] == "on_chat_model_stream" and event["data"]["chunk"].content:
        ...
```

**`ainvoke` vs `astream_events`:**
- `ainvoke` — runs the graph to completion and returns the final state. You get the full response only after Claude has finished generating.
- `astream_events` — runs the graph and yields internal events as they happen. You get tokens as Claude generates them, tool calls as they start, node transitions as they fire.

**`version="v2"`** — LangGraph's streaming API has two versions. v2 is the current stable API with richer event types and more granular information. Always use v2 for new code.

**`on_chat_model_stream`** — the event name fired by LangChain every time the underlying LLM produces a token. The event payload:
```python
event = {
    "event": "on_chat_model_stream",
    "data": {
        "chunk": AIMessageChunk(content="Hello")
    }
}
```

`chunk.content` can be a string or a list of content blocks (for multimodal models or structured responses). The route handles both:
```python
if isinstance(content, list):
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block["text"]
elif isinstance(content, str):
    text = content
```

### EventEncoder

```python
from ag_ui.encoder import EventEncoder
encoder = EventEncoder()
```

`EventEncoder` is the ag-ui-protocol library's serializer. It:
1. Converts each AG-UI event dataclass to a dict
2. Converts field names from snake_case to camelCase (e.g., `thread_id` → `threadId`)
3. JSON-serializes the dict
4. Wraps it in `data: {json}\n\n`
5. Returns the `text/event-stream` content type via `encoder.get_content_type()`

### Request Field Parsing

```python
def _get_field(body: dict, snake: str, camel: str, default=None):
    return body.get(snake) or body.get(camel) or default
```

CopilotKit sends `threadId` and `runId` (camelCase). A raw AG-UI client might send `thread_id` and `run_id` (snake_case). This helper accepts both so the endpoint works with any client.

### Error Handling in Streams

Once you start an SSE response, HTTP status codes are no longer useful — the `200 OK` was already sent with the headers. Errors must be communicated as events:

```python
try:
    result = await segment_graph.ainvoke(...)
    if result.get("error"):
        yield encoder.encode(RunErrorEvent(message=result["error"]))
        return   # ← stops the generator, closes the stream
except Exception as e:
    yield encoder.encode(RunErrorEvent(message=str(e)))
    return
```

The `return` inside an async generator is critical — it signals the generator is exhausted and closes the SSE stream. Without it, the stream would hang.

---

## Frontend — Deep Dive

### Next.js App Router

This project uses Next.js 15 with the App Router (`app/` directory). Key rules:

- **Server Components by default** — files in `app/` are React Server Components unless opted out. Server Components render on the server, have no JS bundle sent to browser, cannot use hooks or browser APIs.
- **`"use client"` directive** — placed at the top of a file, tells Next.js that this file (and everything it imports) should be included in the browser JS bundle and can use React hooks, browser APIs, and event handlers.

Both page files (`chat/page.tsx`, `segment/page.tsx`) are `"use client"` because they use CopilotKit hooks which require browser-side React state.

The **root layout** (`app/layout.tsx`) is intentionally a Server Component — it has no `"use client"` because it only wraps children and imports styles. Server Components can import CSS.

### Next.js API Routes as Backend-for-Frontend

**Files:** `app/api/copilotkit/chat/route.ts`, `app/api/copilotkit/segment/route.ts`

These are **Route Handlers** — server-side code that runs inside the Next.js process. They are not part of the browser bundle. They act as a Backend-for-Frontend (BFF) — a server layer that sits between the browser and your actual backend.

Why not have the browser call the Python backend directly?

1. **CopilotKit's protocol** — `CopilotSidebar` and the hooks send requests to a `CopilotRuntime` endpoint, not raw AG-UI SSE. `CopilotRuntime` translates between CopilotKit's internal format and AG-UI.
2. **Security** — in production you can add authentication, rate limiting, and request validation here before forwarding to the Python backend.
3. **Flexibility** — you could swap the Python backend for any other AG-UI-compatible service without changing the React components.

### CopilotRuntime

```typescript
const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: `${BACKEND_URL}/api/v1/segment`,
      description: "Segment generation agent",
    }),
  },
});
```

`CopilotRuntime` is the server-side orchestrator. It:
- Receives requests from CopilotKit frontend components
- Routes them to the configured agents
- Receives the AG-UI SSE stream from `LangGraphHttpAgent`
- Parses AG-UI events and translates them to CopilotKit's internal wire format
- Streams the translated events back to the browser

**Agent name `"default"`** — this string is the key that links everything together:
- Registered in `CopilotRuntime({ agents: { default: ... } })`
- Referenced by `useCoAgent({ name: "default" })`
- Referenced by `useCoAgentStateRender({ name: "default" })`

If you changed the registration key to `"segment-agent"`, every hook would need to update to `name: "segment-agent"`.

### LangGraphHttpAgent

```typescript
new LangGraphHttpAgent({
  url: `${BACKEND_URL}/api/v1/segment`,
  description: "Segment generation agent",
})
```

Despite the name, `LangGraphHttpAgent` is **not specific to LangGraph**. It is CopilotKit's adapter for any AG-UI-compatible HTTP endpoint. It:
1. Constructs an AG-UI `RunAgentInput` from CopilotKit's internal state
2. POSTs to the configured URL
3. Reads the SSE response line by line
4. Parses each `data: {...}` line as an AG-UI event
5. Translates `STATE_SNAPSHOT` events into CopilotKit agent state (consumed by `useCoAgent` and `useCoAgentStateRender`)
6. Translates `TEXT_MESSAGE_*` events into CopilotKit message objects (displayed by `CopilotSidebar`)

### EmptyAdapter

```typescript
serviceAdapter: new EmptyAdapter()
```

`CopilotRuntime` normally needs an LLM adapter because it can run LLM calls itself (e.g., `OpenAIAdapter`, `AnthropicAdapter`). In this project, **the Python backend does all LLM work** — CopilotKit is purely a protocol translator and UI layer. `EmptyAdapter` tells CopilotRuntime "you have no LLM, everything goes through the agents". It is required by the API signature but does nothing.

Available adapters if you wanted CopilotKit to run LLMs directly:
- `OpenAIAdapter` — uses OpenAI API
- `AnthropicAdapter` — uses Anthropic API directly
- `LangChainAdapter` — wraps any LangChain-compatible model
- `GroqAdapter` — uses Groq for faster inference
- `GoogleGenerativeAIAdapter` — uses Gemini

### copilotRuntimeNextJSAppRouterEndpoint

```typescript
const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter: new EmptyAdapter(),
  endpoint: "/api/copilotkit/segment",
});
return handleRequest(req);
```

This function adapts `CopilotRuntime` to Next.js App Router's `Request`/`Response` API. It:
- Parses the incoming `Request`
- Passes it to `runtime`
- Returns a `Response` (streaming or not)

The `endpoint` parameter must match the URL path of this route handler so CopilotKit can construct correct internal URLs.

---

## CopilotKit UI Components

### CopilotSidebar ← Used in this project

A fixed side panel that slides in from the right. Best for persistent chat that should always be accessible. Props used in this project:

```tsx
<CopilotSidebar
  defaultOpen={true}           // open immediately without user clicking a button
  instructions="..."           // system-level instructions sent with every message
  labels={{
    title: "Segment Builder",  // header text in the sidebar
    initial: "...",            // greeting message before conversation starts, supports markdown
  }}
>
  {children}
</CopilotSidebar>
```

**`instructions`** — this string is injected as system context on every request. It does not appear in the chat history visible to the user, but the agent sees it. In the segment page, this describes the available fields and operators so the agent generates valid conditions.

**`defaultOpen={true}`** — without this, the sidebar starts closed and the user must click a button to open it.

### CopilotPopup ← Not used

```tsx
import { CopilotPopup } from "@copilotkit/react-ui";

<CopilotPopup
  instructions="..."
  labels={{ title: "...", initial: "..." }}
/>
```

A floating chat bubble that appears as a button, toggling an overlay panel when clicked. Best for support-style chat that should not take up screen space by default. The key difference from `CopilotSidebar`: the popup does not wrap children — it floats on top of existing content independently.

### CopilotChat ← Not used

```tsx
import { CopilotChat } from "@copilotkit/react-ui";

<CopilotChat
  instructions="..."
  className="h-full"
/>
```

The raw chat interface without any sidebar or popup wrapper. Renders in-place wherever you put it — useful when you want full control over layout (e.g., embed the chat in a custom panel, split-pane, modal, or drawer that you build yourself).

### CopilotTextarea ← Not used

```tsx
import { CopilotTextarea } from "@copilotkit/react-ui";

<CopilotTextarea
  className="..."
  placeholder="Write a description..."
  autosuggestionsConfig={{
    textareaPurpose: "Describe a user segment",
    chatApiConfigs: {}
  }}
/>
```

A drop-in replacement for `<textarea>` that gains AI-powered autocomplete. As the user types, it suggests completions based on the `textareaPurpose` context. Useful for structured text input like writing segment descriptions, filling in forms with AI assistance, or composing messages.

---

## CopilotKit Hooks — All of Them

### useCoAgent ← Used in this project

**File:** `frontend/app/segment/page.tsx`

```typescript
const { state: segment } = useCoAgent<Segment>({ name: "default" });
```

**Full signature:**
```typescript
function useCoAgent<T>(options: {
  name: string;           // must match agent name in CopilotRuntime
  initialState?: T;       // optional default before any STATE_SNAPSHOT arrives
}): {
  state: T | undefined;   // current agent state, undefined before first snapshot
  setState: (state: T) => void;  // allows frontend to update agent state
  run: (hint?: string) => void;  // programmatically trigger an agent run
  stop: () => void;       // stop an in-progress run
  running: boolean;       // true while the agent is executing
}
```

**What it does:** Subscribes to the agent's state from `STATE_SNAPSHOT` events. Every time a new snapshot arrives, `state` updates and your component re-renders — exactly like `useState` but driven by the SSE stream.

**`setState`** — this is bidirectional. You can push state back to the agent from the frontend. This is useful when you want the UI to modify agent state (e.g., the user edits a segment condition directly in the card, and the agent should know about the change).

**`run` / `stop` / `running`** — programmatic run control. Instead of waiting for the user to type in the chat, you can trigger an agent run from code (e.g., on page load, on button click outside the chat). `running` lets you show a custom loading indicator anywhere on the page.

**State lifetime:** `state` persists as long as the `<CopilotKit>` provider is mounted. Navigating away from the page unmounts the provider, resetting state to `undefined`. This is the automatic page-leave reset behavior.

**TypeScript generic `<Segment>`:** Types the `state` return value. CopilotKit does not validate the shape at runtime — it is purely for editor autocomplete and type checking.

---

### useCoAgentStateRender ← Used in this project

**File:** `frontend/app/segment/page.tsx`

```typescript
useCoAgentStateRender({
  name: "default",
  render: ({ state }) =>
    state?.condition_groups ? <SegmentCard segment={state} /> : null,
});
```

**Full signature:**
```typescript
function useCoAgentStateRender<T>(options: {
  name: string;   // agent name
  render: (props: {
    state: T;
    status: "inProgress" | "complete";
  }) => ReactNode;
}): void
```

**What it does:** Registers a render function that CopilotKit calls to inject a React component **directly into the chat thread**, in the message slot of the current agent run. The component appears where the agent's reply would be — before, alongside, or instead of the text message.

**`status: "inProgress" | "complete"`:**
- `"inProgress"` — the agent is still running. The `STATE_SNAPSHOT` arrived but `RUN_FINISHED` has not yet been emitted. You can use this to show a loading state or a "building..." indicator inside the card.
- `"complete"` — `RUN_FINISHED` was received. The state is final.

Example using status:
```tsx
render: ({ state, status }) => {
  if (!state?.condition_groups) return null;
  return (
    <div>
      <SegmentCard segment={state} />
      {status === "inProgress" && <span>Refining...</span>}
    </div>
  );
}
```

**Per-run scoping:** Each agent run gets its own render slot in the chat history. When the user sends a second message, a new slot is created for the new run. The previous turn's card stays rendered in the chat history.

**Relationship to `useCoAgent`:** Both read from the same `STATE_SNAPSHOT`. `useCoAgentStateRender` controls placement (inside the chat, per-run), while `useCoAgent` gives you the value (outside the chat, any placement, always the latest).

---

### useCopilotAction ← Not used

This is CopilotKit's **Generative UI** hook. It allows the AI agent to trigger frontend actions — both code execution and custom UI rendering inside the chat.

**Full signature:**
```typescript
function useCopilotAction(action: {
  name: string;                          // tool name the agent calls
  description: string;                   // tells the agent what this tool does
  parameters: Parameter[];               // JSON schema for tool arguments
  handler?: (args: Record<string, unknown>) => Promise<unknown>;  // runs when tool is called
  render?: string | ((props: {
    args: Record<string, unknown>;
    status: "inProgress" | "complete";
    result?: unknown;
  }) => ReactNode);                      // JSX to render in the chat for this tool call
}): void
```

**How it differs from `useCoAgentStateRender`:**

| | `useCoAgentStateRender` | `useCopilotAction` |
|---|---|---|
| Triggered by | `STATE_SNAPSHOT` event | Agent calling a named tool |
| Agent awareness | Agent emits state; doesn't know about the render | Agent explicitly decides to call this action |
| Handler | No code execution | `handler` runs arbitrary code |
| Use case | Visualize agent state | Agent-driven UI interactions + code |

**Example — agent navigates the app:**
```tsx
useCopilotAction({
  name: "show_segment_preview",
  description: "Display a preview of the segment being built",
  parameters: [
    { name: "segment_name", type: "string", description: "Name of the segment" },
    { name: "estimated_count", type: "number", description: "Estimated user count" },
  ],
  render: ({ args, status }) => (
    <div className="p-4 border rounded">
      <h3>{args.segment_name}</h3>
      {status === "inProgress" ? "Calculating..." : `~${args.estimated_count} users`}
    </div>
  ),
  handler: async ({ segment_name, estimated_count }) => {
    // This runs when the agent completes the tool call
    console.log("Segment preview shown:", segment_name);
    return "Preview displayed successfully";
  },
});
```

For this to work, the backend agent must know about the `show_segment_preview` tool (passed via the `tools` field in `RunAgentInput`) and must actually call it.

---

### useCopilotReadable ← Not used

Exposes React component state to the AI as context. One-way: frontend → agent.

```typescript
import { useCopilotReadable } from "@copilotkit/react-core";

// In a component:
const [currentPage, setCurrentPage] = useState("segment-builder");
const [userPlan, setUserPlan] = useState("premium");

useCopilotReadable({
  description: "The current page the user is on",
  value: currentPage,
});

useCopilotReadable({
  description: "The user's subscription plan",
  value: userPlan,
});
```

When the user sends a message, CopilotKit includes these as context items in the request. The agent sees them in its context window and can use them to give more relevant responses ("I see you're on the segment builder on a premium plan, so you have access to custom attributes").

This is the frontend equivalent of the `context` field in `RunAgentInput` — `useCopilotReadable` populates that field automatically from React state.

---

### useCopilotChat ← Not used

Programmatic control over the chat — read messages, send messages, clear history from code.

```typescript
import { useCopilotChat } from "@copilotkit/react-core";

const {
  visibleMessages,    // messages currently shown in the chat
  appendMessage,      // add a message programmatically
  setMessages,        // replace the entire message list
  deleteMessage,      // remove a specific message
  reloadMessages,     // re-run the last message
  stopGeneration,     // stop the current streaming response
  isLoading,          // true while waiting for a response
} = useCopilotChat();
```

**Example use cases:**
- Auto-send a message when a user completes an action: "You just created your first segment. Want me to explain it?"
- Clear the chat history when the user clicks "Start Over"
- Pre-populate the chat with a system message based on route parameters
- Read `visibleMessages` to build a custom message renderer outside of `CopilotSidebar`

---

### useCopilotAdditionalInstructions ← Not used

Dynamically append instructions to the agent based on runtime state.

```typescript
import { useCopilotAdditionalInstructions } from "@copilotkit/react-core";

const isPremium = user.plan === "premium";

useCopilotAdditionalInstructions({
  instructions: isPremium
    ? "This user has access to custom attributes and unlimited condition groups."
    : "This user is on the free plan. Limit segments to 2 condition groups.",
  available: "enabled",
});
```

This supplements (not replaces) the `instructions` prop on `CopilotSidebar`. Useful when instructions need to change based on component state, user permissions, or page context that is not known at render time.

---

## The Inner Component Pattern

This pattern appears in `segment/page.tsx` and is a requirement, not a style choice:

```tsx
function SegmentPageContent() {
  // hooks here — useCoAgent, useCoAgentStateRender
  return <div>...</div>;
}

export default function SegmentPage() {
  return (
    <CopilotKit runtimeUrl="...">
      <CopilotSidebar ...>
        <SegmentPageContent />   {/* hooks run inside the provider */}
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

**Why?** React hooks must be called inside a matching context provider. `useCoAgent` and `useCoAgentStateRender` read from CopilotKit's React context, which is established by `<CopilotKit>`. If you called the hooks directly in `SegmentPage` (the component that renders `<CopilotKit>`), they would run before the provider mounts and throw a runtime error.

The solution: move hook calls into a child component (`SegmentPageContent`) that is rendered inside the provider tree.

---

## SegmentCard Component

**File:** `frontend/components/SegmentCard.tsx`

A **pure display component** — no hooks, no side effects, no CopilotKit dependency. Given a `Segment` object, it renders a styled card.

**Interfaces** are defined locally (duplicated from the backend schema). This is intentional — the component has no import dependency on anything outside itself, making it independently testable and reusable.

**Visual structure:**
```
┌────────────────────────────────────────┐
│  Active US Buyers             [Segment]│  ← name (semibold) + purple badge
│  Users from the US who made a purchase │  ← description (small, muted)
├────────────────────────────────────────┤
│  Group 1 · AND                         │  ← group header
│  [country = US] [purchase_count ≥ 1]  │  ← condition chips
│                                        │
│  — OR —                                │  ← separator between groups
│                                        │
│  Group 2 · OR                          │
│  [plan_type = premium]                 │
├────────────────────────────────────────┤
│  Scope: Users matching all criteria    │  ← footer (only if estimated_scope set)
└────────────────────────────────────────┘
```

**Condition chips** use `font-mono` so field names, operators, and values are visually distinct from surrounding text. The `field` part is purple, operator is grey, value is default color.

**Defensive guards:**
```tsx
{(segment.condition_groups ?? []).map(...)}
{(group.conditions ?? []).map(...)}
```

CopilotKit may call `useCoAgentStateRender`'s render function while the state object exists but individual array fields are not yet populated. The `?? []` prevents `.map()` from throwing on `undefined`. The parent also guards with `state?.condition_groups` before rendering the card at all, so in practice you won't see an empty card.

**Used in two contexts:**
1. Inside `useCoAgentStateRender` → renders in the CopilotSidebar chat thread
2. In `SegmentPageContent`'s JSX via `useCoAgent` state → renders in the main content area

---

## Full Data Flows

### Segment Page — Complete Request-to-Render

```
① User types in CopilotSidebar input and presses Enter
   └─ CopilotKit captures message, adds to local message history

② Browser POSTs to /api/copilotkit/segment
   Body (CopilotKit format):
   {
     threadId: "abc",
     runId: "xyz",
     messages: [{ role: "user", content: "US users who purchased" }],
     agentName: "default"
   }

③ copilotRuntimeNextJSAppRouterEndpoint receives the request
   └─ CopilotRuntime routes to the "default" agent (LangGraphHttpAgent)
   └─ LangGraphHttpAgent constructs RunAgentInput (snake_case fields)
   └─ POSTs to http://localhost:8000/api/v1/segment

④ FastAPI route receives RunAgentInput
   └─ _get_field() extracts thread_id and run_id (handles both camel and snake)
   └─ _extract_user_query() gets "US users who purchased" from messages
   └─ StreamingResponse starts with event_stream() generator

⑤ event_stream() begins:
   yield RUN_STARTED { threadId, runId }
   yield STEP_STARTED { stepName: "generate_segment" }

⑥ segment_graph.ainvoke() is called — blocks until Claude responds
   └─ LangGraph runs generate_segment node
   └─ structured_llm.ainvoke() sends to Claude:
      - System prompt (field types, operators, rules)
      - User message: "US users who purchased"
      - Tool definition: JSON schema of Segment model
   └─ Claude responds with tool call (structured JSON)
   └─ LangChain deserializes → Segment instance

⑦ event_stream() continues:
   yield STATE_SNAPSHOT { snapshot: segment.model_dump() }
   └─ snapshot = { name, description, condition_groups, estimated_scope }

⑧ LangGraphHttpAgent receives STATE_SNAPSHOT
   └─ Updates CopilotKit's internal agent state registry

⑨ React re-renders triggered simultaneously:
   ├─ useCoAgentStateRender.render({ state: segment, status: "inProgress" })
   │   └─ state.condition_groups exists → renders <SegmentCard />
   │   └─ CopilotSidebar injects card into the current run's message slot
   │
   └─ useCoAgent state updates: segment = { name, description, condition_groups }
       └─ SegmentPageContent re-renders
       └─ segment?.condition_groups is truthy → renders <SegmentCard /> in main area

⑩ event_stream() continues:
   yield TEXT_MESSAGE_START { messageId, role: "assistant" }
   yield TEXT_MESSAGE_CONTENT { delta: "Created segment: **US Buyers**\n\nUsers..." }
   yield TEXT_MESSAGE_END { messageId }
   └─ CopilotSidebar appends text below the SegmentCard in the chat

⑪ event_stream() finishes:
   yield STEP_FINISHED { stepName: "generate_segment" }
   yield RUN_FINISHED { threadId, runId }
   └─ useCoAgentStateRender.render called again with status: "complete"
   └─ SSE stream closes
```

### Chat Page — Complete Request-to-Render

```
① User types in CopilotSidebar input

② Browser POSTs to /api/copilotkit/chat

③ LangGraphHttpAgent POSTs to http://localhost:8000/api/v1/chat
   with thread_id (same across turns for conversation memory)

④ FastAPI route calls:
   chat_agent.astream_events(
     { messages: [{ role: "user", content: "..." }] },
     config={ configurable: { thread_id: "abc" } },
     version="v2"
   )
   └─ LangGraph loads conversation history for thread_id from checkpointer
   └─ Appends new user message
   └─ Calls Claude (streaming mode)

⑤ As Claude generates tokens, LangGraph fires on_chat_model_stream events
   For each token:
   └─ Route encodes TEXT_MESSAGE_CONTENT { delta: token }
   └─ Yields to SSE stream immediately

⑥ CopilotSidebar receives each TEXT_MESSAGE_CONTENT
   └─ Appends delta to the streaming assistant message bubble
   └─ User sees text appearing in real time, word by word

⑦ When Claude finishes:
   yield TEXT_MESSAGE_END
   yield RUN_FINISHED
   └─ LangGraph checkpointer saves updated conversation history for thread_id
   └─ Next message on this thread will include full history
```

---

## AG-UI Events Not Yet Used

These events are part of the AG-UI protocol spec and could be added to this project with backend changes.

### STATE_DELTA — Incremental State Updates

Instead of sending the full `Segment` on every update, send only what changed using JSON Patch:

```python
# First response: full snapshot
yield StateSnapshotEvent(snapshot=segment.model_dump())

# If agent refines the segment in a second pass:
yield StateDeltaEvent(delta=[
    {"op": "replace", "path": "/name", "value": "Refined US Buyers"},
    {"op": "add", "path": "/condition_groups/0/conditions/-",
     "value": {"field": "age", "operator": "greater_than", "value": 18}}
])
```

Useful when agent state is large and you want to minimize payload size on updates.

### TOOL_CALL_* — Frontend Tool Execution

Allows the backend agent to call frontend functions:

```python
# Backend emits:
yield ToolCallStartEvent(tool_call_id="tc1", tool_call_name="show_user_count")
yield ToolCallArgsEvent(tool_call_id="tc1", delta='{"segment_id": "abc"}')
yield ToolCallEndEvent(tool_call_id="tc1")
```

```tsx
// Frontend handles with useCopilotAction:
useCopilotAction({
  name: "show_user_count",
  description: "Show the estimated user count for a segment",
  parameters: [{ name: "segment_id", type: "string" }],
  handler: async ({ segment_id }) => {
    const count = await fetchUserCount(segment_id);
    return `${count} users match`;
  },
  render: ({ args, status, result }) => (
    <div>{status === "complete" ? `~${result}` : "Counting..."}</div>
  ),
});
```

### MESSAGES_SNAPSHOT — Restore Conversation

```python
yield MessagesSnapshotEvent(messages=[
    {"id": "m1", "role": "user", "content": "Previous question"},
    {"id": "m2", "role": "assistant", "content": "Previous answer"},
])
```

Send this before `RUN_STARTED` to restore a persisted conversation on the frontend.

### CUSTOM — Application-Specific Events

```python
yield CustomEvent(name="confidence_score", value={"score": 0.94, "reason": "clear intent"})
```

The frontend can listen for custom events via CopilotKit's event system or by consuming the SSE stream directly.

### REASONING — Chain of Thought

```python
yield ReasoningEvent(content="The user wants active users from US. I should combine country=US with a recency condition on last_login_date.")
```

For models that support explicit reasoning. Can be rendered in the UI to show the agent's thought process before its final answer.

---

## Tests

**File:** `tests/test_schemas.py`

The test suite validates the Pydantic schema layer — the types and constraints that sit between Claude's output and the application.

**What is tested:**
- All value types for `Condition.value`: `str`, `int`, `float`, `list[str]`
- Valid `logical_operator` values: `"AND"`, `"OR"`
- Invalid `logical_operator` raises `ValidationError` (e.g., `"XOR"`)
- Full `Segment` construction with multiple condition groups
- Serialization roundtrip: `model_dump_json()` → `model_validate_json()` produces equal object
- Optional field: `estimated_scope` defaults to `None`

**Why these tests matter:** `with_structured_output(Segment)` relies on the Pydantic schema being correct. If the schema accepted invalid operators, Claude could return them and they would pass into the `STATE_SNAPSHOT`. The tests ensure the schema correctly rejects invalid data before it reaches the frontend.

**Running tests:**
```bash
just test
# or directly:
uv run pytest tests/
```

---

## How to Extend This Project

### Add a tool the agent can call on the frontend

1. In the segment route, emit `TOOL_CALL_START/ARGS/END` events when the agent invokes a tool
2. Add `useCopilotAction` in `SegmentPageContent` with the matching tool name
3. The `handler` runs locally on the frontend; the return value is sent back to the agent as a tool result

### Add conversation context from the page

```tsx
useCopilotReadable({
  description: "The user's current subscription plan",
  value: "premium",
});
```

The agent will see this when generating segments and can tailor its response (e.g., allowing more complex conditions for premium users).

### Persist conversation history across page reloads

Store the `thread_id` in `localStorage` instead of generating a new UUID on every page load. LangGraph's checkpointer will load the existing conversation history for that thread on the next request.

### Refine the segment across multiple turns

Currently, each request invokes the graph fresh with only the latest user message. To enable iterative refinement (user: "make the age range wider"), pass the current segment state back in the `RunAgentInput.state` field, and update the `generate_segment` node to read and refine it.

### Add a second graph node for validation

After `generate_segment`, add a `validate_segment` node that checks conditions are internally consistent. If validation fails, it can set an error message or auto-correct the segment before emitting the `STATE_SNAPSHOT`.

```python
graph.add_node("validate_segment", validate_node)
graph.add_edge("generate_segment", "validate_segment")
graph.add_edge("validate_segment", END)
```

### Use STATE_DELTA for live segment building

Instead of calling Claude once and returning the full segment, you could stream partial segment state as Claude reasons through the conditions — emitting `STATE_SNAPSHOT` for the initial shell and `STATE_DELTA` as each condition group is determined. This would make the card appear to build itself incrementally.

### Show agent reasoning

Add `ReasoningEvent` in the route before `STATE_SNAPSHOT` and render the reasoning text in a collapsible section in `SegmentCard` or as a separate message in the chat.
