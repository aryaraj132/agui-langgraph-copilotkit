# CopilotKit Frontend Integration Guide

This document explains how to build a CopilotKit-based AG-UI frontend that connects to this backend. It covers setup, configuration, and working with both the **chat agent** and the **segment generation agent**.

> **Reference implementation:** A working frontend is included in the `frontend/` directory. Run `just prepare` then `just frontend` to start it.

## Table of Contents

- [Backend Overview](#backend-overview)
- [Frontend Setup](#frontend-setup)
- [Connecting to the Backend](#connecting-to-the-backend)
- [Chat Agent Integration](#chat-agent-integration)
- [Segment Agent Integration](#segment-agent-integration)
- [AG-UI Event Reference](#ag-ui-event-reference)
- [Request Format](#request-format)
- [Segment State Schema](#segment-state-schema)
- [Error Handling](#error-handling)
- [CORS & Environment](#cors--environment)

---

## Backend Overview

The backend exposes two AG-UI protocol compliant endpoints:

| Method | Path | Agent | Description |
|--------|------|-------|-------------|
| `POST` | `/api/v1/chat` | Chat Agent | General-purpose conversational agent. Streams text tokens via SSE. |
| `POST` | `/api/v1/segment` | Segment Agent | Generates structured user segments from natural language. Emits both `STATE_SNAPSHOT` (structured data) and text messages via SSE. |
| `GET` | `/health` | — | Health check, returns `{"status": "ok"}` |

Both agent endpoints accept an AG-UI `RunAgentInput` body and return AG-UI protocol events over Server-Sent Events (SSE).

The backend runs on `http://localhost:8000` by default.

---

## Frontend Setup

### 1. Create a Next.js App

```bash
npx create-next-app@latest my-agui-frontend --typescript --app
cd my-agui-frontend
```

### 2. Install CopilotKit

```bash
npm install @copilotkit/react-core @copilotkit/react-ui
```

### 3. Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Connecting to the Backend

### Option A: Using CopilotKit's Built-in Runtime

If using CopilotKit's `runtimeUrl` with a Copilot Runtime proxy, point it at your backend. CopilotKit will handle AG-UI event parsing automatically.

```tsx
// app/layout.tsx
"use client";

import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

You would then need a Next.js API route that proxies to this backend.

### Option B: Direct SSE Connection (Recommended for This Backend)

Since this backend implements the AG-UI protocol directly (not through the CopilotKit SDK), you can consume the SSE streams directly. This gives you full control and works with any AG-UI frontend framework.

```tsx
// lib/agui-client.ts
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface RunAgentInput {
  thread_id: string;
  run_id: string;
  messages: Array<{
    id: string;
    role: "user" | "assistant";
    content: string;
  }>;
  tools?: Array<{ name: string; description: string; parameters?: object }>;
  context?: Array<{ description: string; value: string }>;
  state?: Record<string, unknown>;
}

export async function streamAgent(
  endpoint: "chat" | "segment",
  input: RunAgentInput,
  onEvent: (event: AGUIEvent) => void,
): Promise<void> {
  const response = await fetch(`${BACKEND_URL}/api/v1/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }

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
            const event = JSON.parse(jsonStr) as AGUIEvent;
            onEvent(event);
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  }
}

export type AGUIEvent =
  | { type: "RUN_STARTED"; threadId: string; runId: string }
  | { type: "RUN_FINISHED"; threadId: string; runId: string; result?: unknown }
  | { type: "RUN_ERROR"; message: string; code?: string }
  | { type: "STEP_STARTED"; stepName: string }
  | { type: "STEP_FINISHED"; stepName: string }
  | { type: "TEXT_MESSAGE_START"; messageId: string; role: string }
  | { type: "TEXT_MESSAGE_CONTENT"; messageId: string; delta: string }
  | { type: "TEXT_MESSAGE_END"; messageId: string }
  | { type: "STATE_SNAPSHOT"; snapshot: unknown };
```

---

## Chat Agent Integration

The chat agent (`POST /api/v1/chat`) streams text tokens. Here's a complete React component:

```tsx
// components/ChatAgent.tsx
"use client";

import { useState, useCallback } from "react";
import { streamAgent, RunAgentInput } from "@/lib/agui-client";
import { v4 as uuid } from "uuid";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function ChatAgent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId] = useState(() => uuid());

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isStreaming) return;

    const userMsg: Message = { id: uuid(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    const assistantMsgId = uuid();
    let assistantContent = "";

    // Add empty assistant message placeholder
    setMessages((prev) => [
      ...prev,
      { id: assistantMsgId, role: "assistant", content: "" },
    ]);

    const agentInput: RunAgentInput = {
      thread_id: threadId,
      run_id: uuid(),
      messages: [{ id: userMsg.id, role: "user", content: userMsg.content }],
    };

    try {
      await streamAgent("chat", agentInput, (event) => {
        if (event.type === "TEXT_MESSAGE_CONTENT") {
          assistantContent += event.delta;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId ? { ...m, content: assistantContent } : m,
            ),
          );
        }
        // RUN_ERROR is handled in the catch block via the stream
        if (event.type === "RUN_ERROR") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: `Error: ${event.message}` }
                : m,
            ),
          );
        }
      });
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: `Connection error: ${err}` }
            : m,
        ),
      );
    } finally {
      setIsStreaming(false);
    }
  }, [input, isStreaming, threadId]);

  return (
    <div>
      <div style={{ maxHeight: 400, overflowY: "auto", marginBottom: 16 }}>
        {messages.map((msg) => (
          <div key={msg.id} style={{ marginBottom: 8 }}>
            <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>{" "}
            {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        placeholder="Type a message..."
        disabled={isStreaming}
      />
      <button onClick={sendMessage} disabled={isStreaming}>
        Send
      </button>
    </div>
  );
}
```

---

## Segment Agent Integration

The segment agent (`POST /api/v1/segment`) returns both:
- A `STATE_SNAPSHOT` event with the structured segment data
- A `TEXT_MESSAGE_*` sequence with a human-readable summary

```tsx
// components/SegmentAgent.tsx
"use client";

import { useState, useCallback } from "react";
import { streamAgent, RunAgentInput } from "@/lib/agui-client";
import { v4 as uuid } from "uuid";

// Matches the backend Pydantic schema exactly
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

export function SegmentAgent() {
  const [query, setQuery] = useState("");
  const [segment, setSegment] = useState<Segment | null>(null);
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateSegment = useCallback(async () => {
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setSegment(null);
    setSummary("");
    setError(null);

    const input: RunAgentInput = {
      thread_id: uuid(),
      run_id: uuid(),
      messages: [{ id: uuid(), role: "user", content: query }],
    };

    let textContent = "";

    try {
      await streamAgent("segment", input, (event) => {
        switch (event.type) {
          case "STATE_SNAPSHOT":
            // This contains the structured segment data
            setSegment(event.snapshot as Segment);
            break;

          case "TEXT_MESSAGE_CONTENT":
            // Accumulate the human-readable summary
            textContent += event.delta;
            setSummary(textContent);
            break;

          case "RUN_ERROR":
            setError(event.message);
            break;
        }
      });
    } catch (err) {
      setError(`Connection error: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [query, isLoading]);

  return (
    <div>
      <h2>Segment Generator</h2>

      <div style={{ marginBottom: 16 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && generateSegment()}
          placeholder="Describe your target audience..."
          style={{ width: 400 }}
          disabled={isLoading}
        />
        <button onClick={generateSegment} disabled={isLoading}>
          {isLoading ? "Generating..." : "Generate Segment"}
        </button>
      </div>

      {error && <div style={{ color: "red" }}>Error: {error}</div>}

      {summary && (
        <div style={{ marginBottom: 16, fontStyle: "italic" }}>{summary}</div>
      )}

      {segment && (
        <div>
          <h3>{segment.name}</h3>
          <p>{segment.description}</p>
          {segment.estimated_scope && (
            <p><em>Scope: {segment.estimated_scope}</em></p>
          )}

          {segment.condition_groups.map((group, gi) => (
            <div key={gi} style={{ border: "1px solid #ccc", padding: 12, marginBottom: 8 }}>
              <strong>Group ({group.logical_operator})</strong>
              <ul>
                {group.conditions.map((cond, ci) => (
                  <li key={ci}>
                    <code>{cond.field}</code> {cond.operator}{" "}
                    <code>{JSON.stringify(cond.value)}</code>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <details>
            <summary>Raw JSON</summary>
            <pre>{JSON.stringify(segment, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
```

---

## AG-UI Event Reference

Every SSE line from the backend follows the format: `data: {"type": "EVENT_TYPE", ...}\n\n`

Field names are **camelCase** in the JSON (Python snake_case is auto-converted).

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
data: {"type":"STATE_SNAPSHOT","snapshot":{"name":"...","description":"...","conditionGroups":[...]}}
data: {"type":"TEXT_MESSAGE_START","messageId":"...","role":"assistant"}
data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":"Created segment: **Active US Users**\n\n..."}
data: {"type":"TEXT_MESSAGE_END","messageId":"..."}
data: {"type":"STEP_FINISHED","stepName":"generate_segment"}
data: {"type":"RUN_FINISHED","threadId":"...","runId":"..."}
```

### Error Sequence

```
data: {"type":"RUN_STARTED","threadId":"...","runId":"..."}
data: {"type":"RUN_ERROR","message":"API key not configured"}
```

Note: on error, `RUN_FINISHED` is **not** sent — the stream ends after `RUN_ERROR`.

### All Event Types Used

| Event Type | Fields | When |
|-----------|--------|------|
| `RUN_STARTED` | `threadId`, `runId` | First event in every stream |
| `RUN_FINISHED` | `threadId`, `runId`, `result?` | Last event on success |
| `RUN_ERROR` | `message`, `code?` | On failure (terminal) |
| `STEP_STARTED` | `stepName` | Before a graph step (segment only) |
| `STEP_FINISHED` | `stepName` | After a graph step (segment only) |
| `TEXT_MESSAGE_START` | `messageId`, `role` | Before text tokens |
| `TEXT_MESSAGE_CONTENT` | `messageId`, `delta` | Each text token/chunk |
| `TEXT_MESSAGE_END` | `messageId` | After all tokens |
| `STATE_SNAPSHOT` | `snapshot` | Structured data (segment only) |

---

## Request Format

Both endpoints accept the same AG-UI `RunAgentInput` shape:

```typescript
interface RunAgentInput {
  thread_id: string;       // Conversation identifier (for continuity)
  run_id: string;          // Unique per request
  messages: Message[];     // Conversation history
  tools?: Tool[];          // Available tools (optional, not used currently)
  context?: Context[];     // Background context (optional)
  state?: object;          // Agent state (optional)
  forwarded_props?: object; // Custom config (optional)
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string | InputContent[];
}

// For multimodal content
interface InputContent {
  type: "text" | "binary";
  text?: string;         // for type="text"
  mime_type?: string;    // for type="binary"
  data?: string;         // base64 for type="binary"
}
```

**Minimal request example:**

```json
{
  "thread_id": "abc-123",
  "run_id": "run-456",
  "messages": [
    { "id": "msg-1", "role": "user", "content": "Active users from the US" }
  ]
}
```

The backend extracts the **last user message** from the `messages` array as the query. All other fields are optional.

---

## Segment State Schema

The `STATE_SNAPSHOT` event from the segment agent contains this structure:

```typescript
interface Segment {
  name: string;                        // e.g., "Active US Users"
  description: string;                 // Human-readable summary
  condition_groups: ConditionGroup[];
  estimated_scope?: string;            // e.g., "Users matching all criteria"
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
| Behavioral events | `purchase_count`, `last_purchase_date`, `total_spent`, `login_count`, `last_login_date`, `page_views`, `session_duration` |
| Engagement | `email_opened`, `email_clicked`, `push_notification_opened`, `app_opens`, `feature_used` |
| Custom | Any snake_case property name |

### Available Operators

`equals`, `not_equals`, `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`, `contains`, `not_contains`, `starts_with`, `ends_with`, `within_last`, `before`, `after`, `between`, `is_set`, `is_not_set`, `in`, `not_in`

---

## Error Handling

### Backend Errors

When the backend encounters an error, it sends a `RUN_ERROR` event and closes the stream:

```json
{"type": "RUN_ERROR", "message": "Anthropic API key not set"}
```

Check for this event type and display the `message` field to the user.

### Connection Errors

If `fetch()` fails (backend down, network issue), handle it in the `catch` block:

```typescript
try {
  await streamAgent("chat", input, onEvent);
} catch (err) {
  // Backend is unreachable
  showError(`Cannot connect to backend: ${err}`);
}
```

### Missing API Key

The backend requires `ANTHROPIC_API_KEY` to be set. If missing, agents will fail at startup and the server won't start. Verify with:

```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

---

## CORS & Environment

### Development

The backend allows all origins (`Access-Control-Allow-Origin: *`) with `allow_credentials=False`. No special CORS configuration is needed on the frontend during development.

### Production

For production, update the backend's CORS config in `main.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Backend Default Port

The backend runs on **port 8000**. To change it, modify `main.py` or run:

```bash
uv run uvicorn agui_backend_demo.main:app --host 0.0.0.0 --port 3001
```
