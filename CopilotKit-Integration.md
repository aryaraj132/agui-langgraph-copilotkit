# CopilotKit Frontend Integration Guide

This document explains how the CopilotKit frontend in `frontend/` connects to the AG-UI backend, and how to build your own. It covers setup, the Next.js API route bridge, and all CopilotKit patterns used.

> **Reference implementation:** A working frontend is in `frontend/`. Run `just prepare` then start both servers with `just backend` and `just frontend`.

---

## Table of Contents

- [Backend Overview](#backend-overview)
- [Frontend Setup](#frontend-setup)
- [Connecting to the Backend — CopilotKit Runtime](#connecting-to-the-backend--copilotkit-runtime)
- [Chat Page — Actual Implementation](#chat-page--actual-implementation)
- [Segment Page — Actual Implementation](#segment-page--actual-implementation)
- [useCoAgentStateRender — Render Inside the Chat](#usecoagentstatrender--render-inside-the-chat)
- [useCoAgent — Render Outside the Chat](#usecoagent--render-outside-the-chat)
- [SegmentCard Component](#segmentcard-component)
- [AG-UI Event Reference](#ag-ui-event-reference)
- [Segment State Schema](#segment-state-schema)
- [Alternative: Raw SSE Without CopilotKit](#alternative-raw-sse-without-copilotkit)
- [Error Handling](#error-handling)
- [CORS & Environment](#cors--environment)

---

## Backend Overview

The backend exposes two AG-UI protocol compliant endpoints:

| Method | Path | Agent | Description |
|--------|------|-------|-------------|
| `POST` | `/api/v1/chat` | Chat Agent | Streams text tokens via SSE. Maintains conversation history per `thread_id`. |
| `POST` | `/api/v1/segment` | Segment Agent | Emits `STATE_SNAPSHOT` (structured `Segment` object) + text summary via SSE. |
| `GET` | `/health` | — | Health check → `{"status": "ok"}` |

Both endpoints accept an AG-UI `RunAgentInput` body and stream AG-UI protocol events. The backend runs on `http://localhost:8000` by default.

---

## Frontend Setup

### 1. Create a Next.js App

```bash
npx create-next-app@latest my-agui-frontend --typescript --app
cd my-agui-frontend
```

### 2. Install CopilotKit

```bash
npm install @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime
```

- `@copilotkit/react-core` — hooks (`useCoAgent`, `useCoAgentStateRender`, etc.) and the `CopilotKit` provider
- `@copilotkit/react-ui` — UI components (`CopilotSidebar`, `CopilotPopup`, `CopilotChat`)
- `@copilotkit/runtime` — server-side `CopilotRuntime` and `LangGraphHttpAgent` (used in Next.js API routes)

### 3. Import CopilotKit Styles

In your root layout (not in individual pages):

```tsx
// app/layout.tsx
import "@copilotkit/react-ui/styles.css";
```

### 4. Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

The `NEXT_PUBLIC_` prefix makes this variable available in the browser bundle. Without it, Next.js strips it from client-side code.

---

## Connecting to the Backend — CopilotKit Runtime

The frontend does not call the Python backend directly. Instead:

1. CopilotKit components (`CopilotSidebar`, etc.) POST to a **Next.js API route** in your app
2. That API route runs `CopilotRuntime` + `LangGraphHttpAgent` on the server
3. `LangGraphHttpAgent` forwards the request to the Python backend and parses the AG-UI SSE stream
4. CopilotKit translates the events and streams them back to the browser

This indirection is required because CopilotKit's internal wire format is not the same as raw AG-UI — `CopilotRuntime` handles the translation.

### Next.js API Route (one per agent)

The actual implementation uses **separate routes per agent**, each with its own `CopilotRuntime` pointing at a different backend endpoint.

**`app/api/copilotkit/chat/route.ts`**

```typescript
import {
  CopilotRuntime,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: `${BACKEND_URL}/api/v1/chat`,
      description: "General-purpose chat agent",
    }),
  },
});

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new EmptyAdapter(),
    endpoint: "/api/copilotkit/chat",
  });
  return handleRequest(req);
};
```

**`app/api/copilotkit/segment/route.ts`**

```typescript
import {
  CopilotRuntime,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: `${BACKEND_URL}/api/v1/segment`,
      description: "Segment generation agent",
    }),
  },
});

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new EmptyAdapter(),
    endpoint: "/api/copilotkit/segment",
  });
  return handleRequest(req);
};
```

**Key points:**
- `LangGraphHttpAgent` is CopilotKit's adapter for any AG-UI-compliant endpoint (not just LangGraph)
- `EmptyAdapter` signals that CopilotKit is not running its own LLM — the Python backend does all LLM work
- The agent name `"default"` must match what the frontend hooks reference (`useCoAgent({ name: "default" })`)
- `endpoint` must match the route's URL path so CopilotKit can construct internal URLs correctly

---

## Chat Page — Actual Implementation

**`app/chat/page.tsx`**

```tsx
"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";

export default function ChatPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/chat">
      <CopilotSidebar
        defaultOpen={true}
        labels={{
          title: "Chat",
          initial: "Hi! I'm powered by Claude, running on the AG-UI backend.\nNo AI on the frontend — ask me anything!",
        }}
      >
        <div className="h-screen flex flex-col">
          <Nav />
          <main className="flex-1 flex items-center justify-center text-gray-400">
            <p className="text-sm">Chat Agent — all LLM calls happen on the Python backend.</p>
          </main>
        </div>
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

**What's happening:**
- `<CopilotKit runtimeUrl="/api/copilotkit/chat">` — establishes the connection to the chat API route. All CopilotKit hooks inside this provider talk to this runtime.
- `<CopilotSidebar>` — renders the full chat UI (message list, input, streaming text display)
- `labels.initial` — the greeting shown before any conversation. Supports markdown.
- No hooks needed — the chat agent only streams text, which `CopilotSidebar` handles automatically

---

## Segment Page — Actual Implementation

The segment page is more involved because the agent emits `STATE_SNAPSHOT` in addition to text. Two hooks are used to surface that state in two places simultaneously.

**`app/segment/page.tsx`**

```tsx
"use client";

import { CopilotKit, useCoAgentStateRender, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { SegmentCard } from "@/components/SegmentCard";

interface Segment {
  name: string;
  description: string;
  condition_groups: Array<{
    logical_operator: "AND" | "OR";
    conditions: Array<{ field: string; operator: string; value: string | number | string[] }>;
  }>;
  estimated_scope?: string;
}

// Inner component — hooks must run inside <CopilotKit>, which is in the outer component
function SegmentPageContent() {
  // Renders <SegmentCard> inline inside the chat thread when STATE_SNAPSHOT arrives
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.condition_groups ? <SegmentCard segment={state} /> : null,
  });

  // Reads the same STATE_SNAPSHOT into React state — drives the card outside the chat
  const { state: segment } = useCoAgent<Segment>({ name: "default" });

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {segment?.condition_groups ? (
          <div className="w-full max-w-lg">
            <SegmentCard segment={segment} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe your audience in the sidebar to generate a segment.
          </p>
        )}
      </main>
    </div>
  );
}

export default function SegmentPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/segment">
      <CopilotSidebar
        defaultOpen={true}
        instructions="You are a user segmentation assistant. The user will describe a target audience and you will generate a structured segment definition with conditions. Available fields include: age, gender, country, city, signup_date, plan_type, purchase_count, total_spent, login_count, email_opened, email_clicked, app_opens, feature_used. Available operators: equals, not_equals, greater_than, less_than, contains, within_last, before, after, between, is_set, is_not_set, in, not_in."
        labels={{
          title: "Segment Builder",
          initial: "Describe your target audience and I'll generate a structured segment.\n\nTry: **\"Users from the US who signed up in the last 30 days and made a purchase\"**",
        }}
      >
        <SegmentPageContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

**Why the inner component pattern?**
React hooks must be called inside their context provider. `useCoAgent` and `useCoAgentStateRender` read from CopilotKit's context, which is established by `<CopilotKit>`. If you called those hooks directly in `SegmentPage` (the component that renders `<CopilotKit>`), they would run before the provider mounts and throw an error. The solution: move hook calls into `SegmentPageContent`, which renders *inside* the provider.

---

## useCoAgentStateRender — Render Inside the Chat

```typescript
useCoAgentStateRender({
  name: "default",
  render: ({ state, status }) =>
    state?.condition_groups ? <SegmentCard segment={state} /> : null,
});
```

**What it does:** Injects a React component directly into the chat thread, in the message slot of the current agent run. The component appears where the agent's reply would be — before the text message.

**`render` function parameters:**
- `state` — the agent state from the latest `STATE_SNAPSHOT`. Will be `undefined` before the first snapshot arrives.
- `status: "inProgress" | "complete"` — `"inProgress"` while the agent is still running (between `RUN_STARTED` and `RUN_FINISHED`), `"complete"` after the run finishes. Use this to show loading indicators or lock the card UI.

**Guard `state?.condition_groups`** — CopilotKit may call `render` while state exists but is only partially populated (individual fields can be `undefined`). Always guard array fields before rendering.

**Per-run scoping** — each agent run gets its own render slot. When the user sends a second message, a new slot is created. Previous turns keep their rendered cards in the chat history.

**Example using `status`:**
```tsx
render: ({ state, status }) => {
  if (!state?.condition_groups) return null;
  return (
    <>
      <SegmentCard segment={state} />
      {status === "inProgress" && (
        <p className="text-xs text-gray-400 mt-1">Refining...</p>
      )}
    </>
  );
}
```

---

## useCoAgent — Render Outside the Chat

```typescript
const { state: segment } = useCoAgent<Segment>({ name: "default" });
```

**What it does:** Subscribes to the agent's state as a React value. Every `STATE_SNAPSHOT` event updates `state` and triggers a re-render — exactly like `useState` but driven by the SSE stream.

**Full return type:**
```typescript
{
  state: Segment | undefined;              // undefined before first snapshot
  setState: (state: Segment) => void;      // push state back to the agent
  run: (hint?: string) => void;            // trigger a run programmatically
  stop: () => void;                        // abort an in-progress run
  running: boolean;                        // true while agent is executing
}
```

**State lifetime:** Persists while `<CopilotKit>` is mounted. Navigating away unmounts the provider and resets state to `undefined` automatically — no cleanup needed.

**`setState`** — bidirectional sync. The frontend can modify agent state directly (e.g., user edits a condition in the card, and the agent should be aware on the next run).

**`run` / `stop` / `running`** — lets you trigger runs from code rather than the chat input, and show loading state anywhere on the page:
```tsx
const { run, running } = useCoAgent({ name: "default" });

<button onClick={() => run("Generate a default segment")} disabled={running}>
  {running ? "Generating..." : "Auto-Generate"}
</button>
```

---

## SegmentCard Component

**`components/SegmentCard.tsx`**

A pure display component — no hooks, no CopilotKit dependency. Takes a `Segment` prop and renders it as a styled card. Safe to use anywhere, including inside `useCoAgentStateRender`.

```tsx
interface Condition {
  field: string;
  operator: string;
  value: string | number | string[];
}

interface ConditionGroup {
  logical_operator: "AND" | "OR";
  conditions: Condition[];
}

interface Segment {
  name: string;
  description: string;
  condition_groups: ConditionGroup[];
  estimated_scope?: string;
}

export function SegmentCard({ segment }: { segment: Segment }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden text-sm my-2 w-full">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {segment.name}
          </span>
          <span className="shrink-0 text-xs bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 px-2 py-0.5 rounded-full">
            Segment
          </span>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mt-1 text-xs">
          {segment.description}
        </p>
      </div>

      <div className="px-4 py-3 space-y-4">
        {(segment.condition_groups ?? []).map((group, gi) => (
          <div key={gi}>
            {gi > 0 && (
              <div className="text-xs text-gray-400 font-medium text-center mb-3">
                — OR —
              </div>
            )}
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">
              Group {gi + 1} &middot; {group.logical_operator}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(group.conditions ?? []).map((cond, ci) => (
                <span
                  key={ci}
                  className="inline-flex items-center gap-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-2 py-1 rounded-md text-xs font-mono"
                >
                  <span className="text-purple-600 dark:text-purple-400">{cond.field}</span>
                  <span className="text-gray-400">{cond.operator}</span>
                  <span>
                    {Array.isArray(cond.value)
                      ? cond.value.join(", ")
                      : String(cond.value)}
                  </span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {segment.estimated_scope && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          Scope: {segment.estimated_scope}
        </div>
      )}
    </div>
  );
}
```

---

## AG-UI Event Reference

Every SSE line from the backend:

```
data: {"type": "EVENT_TYPE", "camelCaseField": "value"}\n\n
```

Top-level event fields use **camelCase** (the Python backend's snake_case is converted by the `ag-ui-protocol` encoder). However, the **`snapshot` dict content** (from `segment.model_dump()`) retains **snake_case** keys — this is what `useCoAgent` returns and what `SegmentCard` reads.

### Chat Agent Event Sequence

```
data: {"type":"RUN_STARTED","threadId":"...","runId":"..."}
data: {"type":"TEXT_MESSAGE_START","messageId":"...","role":"assistant"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":"Hello"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":" there"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":"!"}
data: {"type":"TEXT_MESSAGE_END","messageId":"..."}
data: {"type":"RUN_FINISHED","threadId":"...","runId":"..."}
```

### Segment Agent Event Sequence

```
data: {"type":"RUN_STARTED","threadId":"...","runId":"..."}
data: {"type":"STEP_STARTED","stepName":"generate_segment"}
data: {"type":"STATE_SNAPSHOT","snapshot":{"name":"Active US Buyers","description":"...","condition_groups":[{"logical_operator":"AND","conditions":[{"field":"country","operator":"equals","value":"US"}]}],"estimated_scope":"..."}}
data: {"type":"TEXT_MESSAGE_START","messageId":"...","role":"assistant"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":"Created segment: **Active US Buyers**\n\n..."}
data: {"type":"TEXT_MESSAGE_END","messageId":"..."}
data: {"type":"STEP_FINISHED","stepName":"generate_segment"}
data: {"type":"RUN_FINISHED","threadId":"...","runId":"..."}
```

Note: `snapshot` keys are **snake_case** (`condition_groups`, not `conditionGroups`) — they come from Pydantic's `model_dump()` which preserves the Python field names.

### Error Sequence

```
data: {"type":"RUN_STARTED","threadId":"...","runId":"..."}
data: {"type":"RUN_ERROR","message":"API key not configured"}
```

On error, `RUN_FINISHED` is **not** sent. The stream closes after `RUN_ERROR`.

### All Event Types

| Event Type | Fields | When |
|-----------|--------|------|
| `RUN_STARTED` | `threadId`, `runId` | First event in every stream |
| `RUN_FINISHED` | `threadId`, `runId` | Last event on success |
| `RUN_ERROR` | `message`, `code?` | On failure (terminal) |
| `STEP_STARTED` | `stepName` | Before a graph node (segment only) |
| `STEP_FINISHED` | `stepName` | After a graph node (segment only) |
| `TEXT_MESSAGE_START` | `messageId`, `role` | Before text tokens |
| `TEXT_MESSAGE_CONTENT` | `messageId`, `delta` | Each text token/chunk |
| `TEXT_MESSAGE_END` | `messageId` | After all tokens |
| `STATE_SNAPSHOT` | `snapshot` | Structured segment data (segment only) |

---

## Segment State Schema

The `STATE_SNAPSHOT.snapshot` object matches the backend Pydantic schema exactly, with **snake_case** keys:

```typescript
interface Segment {
  name: string;                        // e.g., "Active US Users"
  description: string;                 // Human-readable summary
  condition_groups: ConditionGroup[];  // snake_case — matches model_dump() output
  estimated_scope?: string;            // Optional, e.g., "Users matching all criteria"
}

interface ConditionGroup {
  logical_operator: "AND" | "OR";
  conditions: Condition[];
}

interface Condition {
  field: string;       // e.g., "country", "age", "purchase_count"
  operator: string;    // e.g., "equals", "greater_than", "within_last"
  value: string | number | string[];
}
```

### Available Fields

| Category | Fields |
|----------|--------|
| User properties | `age`, `gender`, `country`, `city`, `language`, `signup_date`, `plan_type`, `account_status` |
| Behavioral | `purchase_count`, `last_purchase_date`, `total_spent`, `login_count`, `last_login_date`, `page_views`, `session_duration` |
| Engagement | `email_opened`, `email_clicked`, `push_notification_opened`, `app_opens`, `feature_used` |
| Custom | Any snake_case property name |

### Available Operators

`equals`, `not_equals`, `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`, `contains`, `not_contains`, `starts_with`, `ends_with`, `within_last`, `before`, `after`, `between`, `is_set`, `is_not_set`, `in`, `not_in`

---

## Alternative: Raw SSE Without CopilotKit

You can consume this backend directly without CopilotKit using a raw `fetch` + SSE parser. This gives full control at the cost of building your own UI.

### SSE Client

```typescript
// lib/agui-client.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export type AGUIEvent =
  | { type: "RUN_STARTED"; threadId: string; runId: string }
  | { type: "RUN_FINISHED"; threadId: string; runId: string }
  | { type: "RUN_ERROR"; message: string; code?: string }
  | { type: "STEP_STARTED"; stepName: string }
  | { type: "STEP_FINISHED"; stepName: string }
  | { type: "TEXT_MESSAGE_START"; messageId: string; role: string }
  | { type: "TEXT_MESSAGE_CONTENT"; messageId: string; delta: string }
  | { type: "TEXT_MESSAGE_END"; messageId: string }
  | { type: "STATE_SNAPSHOT"; snapshot: unknown };

export async function streamAgent(
  endpoint: "chat" | "segment",
  input: { thread_id: string; run_id: string; messages: Array<{ id: string; role: string; content: string }> },
  onEvent: (event: AGUIEvent) => void,
): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) throw new Error(`Backend returned ${response.status}`);

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const jsonStr = line.slice(6).trim();
        if (jsonStr) {
          try {
            onEvent(JSON.parse(jsonStr) as AGUIEvent);
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  }
}
```

### Raw Chat Component

```tsx
"use client";
import { useState, useCallback } from "react";
import { streamAgent } from "@/lib/agui-client";

export function RawChatAgent() {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);

  const send = useCallback(async () => {
    if (!input.trim() || streaming) return;
    const userContent = input;
    setMessages(m => [...m, { role: "user", content: userContent }]);
    setInput("");
    setStreaming(true);

    let assistantContent = "";
    setMessages(m => [...m, { role: "assistant", content: "" }]);

    await streamAgent("chat", {
      thread_id: "demo",
      run_id: crypto.randomUUID(),
      messages: [{ id: crypto.randomUUID(), role: "user", content: userContent }],
    }, (event) => {
      if (event.type === "TEXT_MESSAGE_CONTENT") {
        assistantContent += event.delta;
        setMessages(m => [...m.slice(0, -1), { role: "assistant", content: assistantContent }]);
      }
    });

    setStreaming(false);
  }, [input, streaming]);

  return (
    <div>
      {messages.map((m, i) => (
        <div key={i}><strong>{m.role}:</strong> {m.content}</div>
      ))}
      <input value={input} onChange={e => setInput(e.target.value)}
        onKeyDown={e => e.key === "Enter" && send()} disabled={streaming} />
      <button onClick={send} disabled={streaming}>Send</button>
    </div>
  );
}
```

### Raw Segment Component

```tsx
"use client";
import { useState, useCallback } from "react";
import { streamAgent } from "@/lib/agui-client";

interface Segment {
  name: string;
  description: string;
  condition_groups: Array<{
    logical_operator: "AND" | "OR";
    conditions: Array<{ field: string; operator: string; value: string | number | string[] }>;
  }>;
  estimated_scope?: string;
}

export function RawSegmentAgent() {
  const [segment, setSegment] = useState<Segment | null>(null);
  const [summary, setSummary] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async () => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setSegment(null);
    setSummary("");
    setError(null);
    let text = "";

    await streamAgent("segment", {
      thread_id: crypto.randomUUID(),
      run_id: crypto.randomUUID(),
      messages: [{ id: crypto.randomUUID(), role: "user", content: query }],
    }, (event) => {
      switch (event.type) {
        case "STATE_SNAPSHOT":
          setSegment(event.snapshot as Segment);
          break;
        case "TEXT_MESSAGE_CONTENT":
          text += event.delta;
          setSummary(text);
          break;
        case "RUN_ERROR":
          setError(event.message);
          break;
      }
    }).catch(err => setError(String(err)));

    setLoading(false);
  }, [query, loading]);

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)}
        onKeyDown={e => e.key === "Enter" && generate()} disabled={loading} />
      <button onClick={generate} disabled={loading}>
        {loading ? "Generating..." : "Generate"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {summary && <p>{summary}</p>}
      {segment && (
        <div>
          <h3>{segment.name}</h3>
          <p>{segment.description}</p>
          {segment.condition_groups.map((g, gi) => (
            <div key={gi}>
              <strong>Group ({g.logical_operator})</strong>
              <ul>
                {g.conditions.map((c, ci) => (
                  <li key={ci}><code>{c.field}</code> {c.operator} <code>{JSON.stringify(c.value)}</code></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Error Handling

### Backend Errors

When the backend encounters an error, it sends `RUN_ERROR` and closes the stream:

```json
{ "type": "RUN_ERROR", "message": "Anthropic API key not set" }
```

With CopilotKit, errors are shown automatically in the sidebar. With raw SSE, handle the event explicitly.

### Connection Errors

If the backend is unreachable, `fetch()` will throw. Wrap your call in `try/catch`.

### Verifying Backend Health

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

---

## CORS & Environment

### Development

The backend allows all origins (`Access-Control-Allow-Origin: *`) with `allow_credentials=False`. No frontend CORS config needed.

### Production

Update `main.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Changing the Backend Port

```bash
uv run uvicorn agui_backend_demo.main:app --host 0.0.0.0 --port 3001
```

Update `NEXT_PUBLIC_BACKEND_URL` in `.env.local` to match.
