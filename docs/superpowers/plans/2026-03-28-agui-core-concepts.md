# AG-UI Core Concepts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 11 AG-UI core concepts across 5 email marketing agents with full documentation, thread persistence, and concept-specific demonstrations.

**Architecture:** Agent-per-module structure where each agent is a self-contained folder (`routes.py`, `graph.py`, `state.py`, `README.md`) registered as a FastAPI `APIRouter`. Shared infrastructure lives in `core/` (event emitter, thread store, middleware). Frontend uses CopilotKit with per-agent pages, shared types, and custom hooks.

**Tech Stack:** Python 3.13, FastAPI, LangGraph, LangChain/Anthropic, ag-ui-protocol, Pydantic | Next.js 15, React 19, CopilotKit 1.8, Tailwind CSS 4, TypeScript 5

---

## Phase 1: Backend Core Infrastructure

### Task 1: Create core module with event emitter

**Files:**
- Create: `src/agui_backend_demo/core/__init__.py`
- Create: `src/agui_backend_demo/core/events.py`
- Test: `tests/test_core_events.py`

- [ ] **Step 1: Create core package init**

```python
# src/agui_backend_demo/core/__init__.py
```

- [ ] **Step 2: Write tests for event emitter**

```python
# tests/test_core_events.py
import json

from agui_backend_demo.core.events import EventEmitter, extract_user_query, get_field


def test_emit_run_started_contains_type():
    emitter = EventEmitter()
    result = emitter.emit_run_started("thread-1", "run-1")
    assert "data:" in result
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "RUN_STARTED"
    assert payload["threadId"] == "thread-1"
    assert payload["runId"] == "run-1"


def test_emit_run_finished_contains_type():
    emitter = EventEmitter()
    result = emitter.emit_run_finished("thread-1", "run-1")
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "RUN_FINISHED"


def test_emit_run_error():
    emitter = EventEmitter()
    result = emitter.emit_run_error("something failed")
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "RUN_ERROR"
    assert payload["message"] == "something failed"


def test_emit_text_message_sequence():
    emitter = EventEmitter()
    start = emitter.emit_text_start("msg-1", "assistant")
    content = emitter.emit_text_content("msg-1", "hello")
    end = emitter.emit_text_end("msg-1")
    for event_str, expected_type in [
        (start, "TEXT_MESSAGE_START"),
        (content, "TEXT_MESSAGE_CONTENT"),
        (end, "TEXT_MESSAGE_END"),
    ]:
        payload = json.loads(event_str.split("data: ", 1)[1].split("\n")[0])
        assert payload["type"] == expected_type
        assert payload["messageId"] == "msg-1"


def test_emit_state_snapshot():
    emitter = EventEmitter()
    result = emitter.emit_state_snapshot({"key": "value"})
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "STATE_SNAPSHOT"
    assert payload["snapshot"] == {"key": "value"}


def test_emit_state_delta():
    emitter = EventEmitter()
    ops = [{"op": "replace", "path": "/name", "value": "new"}]
    result = emitter.emit_state_delta(ops)
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "STATE_DELTA"
    assert payload["delta"] == ops


def test_emit_step_events():
    emitter = EventEmitter()
    start = emitter.emit_step_start("my_step")
    finish = emitter.emit_step_finish("my_step")
    p1 = json.loads(start.split("data: ", 1)[1].split("\n")[0])
    p2 = json.loads(finish.split("data: ", 1)[1].split("\n")[0])
    assert p1["type"] == "STEP_STARTED"
    assert p1["stepName"] == "my_step"
    assert p2["type"] == "STEP_FINISHED"


def test_emit_tool_call_events():
    emitter = EventEmitter()
    start = emitter.emit_tool_call_start("tc-1", "my_tool", "msg-1")
    args = emitter.emit_tool_call_args("tc-1", '{"x": 1}')
    end = emitter.emit_tool_call_end("tc-1")
    for event_str, expected_type in [
        (start, "TOOL_CALL_START"),
        (args, "TOOL_CALL_ARGS"),
        (end, "TOOL_CALL_END"),
    ]:
        payload = json.loads(event_str.split("data: ", 1)[1].split("\n")[0])
        assert payload["type"] == expected_type
        assert payload["toolCallId"] == "tc-1"


def test_emit_activity_snapshot():
    emitter = EventEmitter()
    result = emitter.emit_activity_snapshot("msg-1", "processing", {"title": "Working"})
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "ACTIVITY_SNAPSHOT"
    assert payload["messageId"] == "msg-1"
    assert payload["activityType"] == "processing"


def test_emit_reasoning_sequence():
    emitter = EventEmitter()
    start = emitter.emit_reasoning_start("msg-1")
    msg_start = emitter.emit_reasoning_message_start("msg-1")
    content = emitter.emit_reasoning_content("msg-1", "thinking...")
    msg_end = emitter.emit_reasoning_message_end("msg-1")
    end = emitter.emit_reasoning_end("msg-1")
    types = []
    for event_str in [start, msg_start, content, msg_end, end]:
        payload = json.loads(event_str.split("data: ", 1)[1].split("\n")[0])
        types.append(payload["type"])
    assert types == [
        "REASONING_START",
        "REASONING_MESSAGE_START",
        "REASONING_MESSAGE_CONTENT",
        "REASONING_MESSAGE_END",
        "REASONING_END",
    ]


def test_emit_custom_event():
    emitter = EventEmitter()
    result = emitter.emit_custom("my_event", {"data": 42})
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "CUSTOM"
    assert payload["name"] == "my_event"
    assert payload["value"] == {"data": 42}


def test_emit_messages_snapshot():
    emitter = EventEmitter()
    msgs = [{"id": "m1", "role": "user", "content": "hello"}]
    result = emitter.emit_messages_snapshot(msgs)
    payload = json.loads(result.split("data: ", 1)[1].split("\n")[0])
    assert payload["type"] == "MESSAGES_SNAPSHOT"
    assert payload["messages"] == msgs


def test_get_field_snake_case():
    assert get_field({"thread_id": "t1"}, "thread_id", "threadId") == "t1"


def test_get_field_camel_case():
    assert get_field({"threadId": "t1"}, "thread_id", "threadId") == "t1"


def test_get_field_default():
    assert get_field({}, "thread_id", "threadId", "default") == "default"


def test_extract_user_query_string_content():
    messages = [{"role": "user", "content": "hello"}]
    assert extract_user_query(messages) == "hello"


def test_extract_user_query_list_content():
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "hi there"}]}
    ]
    assert extract_user_query(messages) == "hi there"


def test_extract_user_query_empty():
    assert extract_user_query([]) == ""
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_core_events.py -v`
Expected: FAIL (ImportError — module doesn't exist yet)

- [ ] **Step 4: Implement event emitter**

```python
# src/agui_backend_demo/core/events.py
from ag_ui.core import (
    ActivitySnapshotEvent,
    CustomEvent,
    MessagesSnapshotEvent,
    ReasoningEndEvent,
    ReasoningMessageContentEvent,
    ReasoningMessageEndEvent,
    ReasoningMessageStartEvent,
    ReasoningStartEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateDeltaEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder


def get_field(body: dict, snake: str, camel: str, default=None):
    """Get a field accepting both snake_case and camelCase (AG-UI uses camelCase)."""
    return body.get(snake) or body.get(camel) or default


def extract_user_query(messages: list) -> str:
    """Extract content from the last user message."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part["text"]
            else:
                return content
    return ""


class EventEmitter:
    """Convenience wrapper around EventEncoder for emitting AG-UI events."""

    def __init__(self):
        self._encoder = EventEncoder()

    @property
    def content_type(self) -> str:
        return self._encoder.get_content_type()

    def emit_run_started(self, thread_id: str, run_id: str) -> str:
        return self._encoder.encode(
            RunStartedEvent(thread_id=thread_id, run_id=run_id)
        )

    def emit_run_finished(self, thread_id: str, run_id: str) -> str:
        return self._encoder.encode(
            RunFinishedEvent(thread_id=thread_id, run_id=run_id)
        )

    def emit_run_error(self, message: str) -> str:
        return self._encoder.encode(RunErrorEvent(message=message))

    def emit_step_start(self, step_name: str) -> str:
        return self._encoder.encode(StepStartedEvent(step_name=step_name))

    def emit_step_finish(self, step_name: str) -> str:
        return self._encoder.encode(StepFinishedEvent(step_name=step_name))

    def emit_text_start(self, message_id: str, role: str) -> str:
        return self._encoder.encode(
            TextMessageStartEvent(message_id=message_id, role=role)
        )

    def emit_text_content(self, message_id: str, delta: str) -> str:
        return self._encoder.encode(
            TextMessageContentEvent(message_id=message_id, delta=delta)
        )

    def emit_text_end(self, message_id: str) -> str:
        return self._encoder.encode(
            TextMessageEndEvent(message_id=message_id)
        )

    def emit_state_snapshot(self, snapshot: dict) -> str:
        return self._encoder.encode(StateSnapshotEvent(snapshot=snapshot))

    def emit_state_delta(self, delta: list) -> str:
        return self._encoder.encode(StateDeltaEvent(delta=delta))

    def emit_tool_call_start(
        self, tool_call_id: str, tool_call_name: str, parent_message_id: str | None = None
    ) -> str:
        return self._encoder.encode(
            ToolCallStartEvent(
                toolCallId=tool_call_id,
                toolCallName=tool_call_name,
                parentMessageId=parent_message_id,
            )
        )

    def emit_tool_call_args(self, tool_call_id: str, delta: str) -> str:
        return self._encoder.encode(
            ToolCallArgsEvent(toolCallId=tool_call_id, delta=delta)
        )

    def emit_tool_call_end(self, tool_call_id: str) -> str:
        return self._encoder.encode(
            ToolCallEndEvent(toolCallId=tool_call_id)
        )

    def emit_activity_snapshot(
        self, message_id: str, activity_type: str, content: dict, replace: bool = True
    ) -> str:
        return self._encoder.encode(
            ActivitySnapshotEvent(
                messageId=message_id,
                activityType=activity_type,
                content=content,
                replace=replace,
            )
        )

    def emit_reasoning_start(self, message_id: str) -> str:
        return self._encoder.encode(
            ReasoningStartEvent(messageId=message_id)
        )

    def emit_reasoning_message_start(self, message_id: str) -> str:
        return self._encoder.encode(
            ReasoningMessageStartEvent(messageId=message_id, role="reasoning")
        )

    def emit_reasoning_content(self, message_id: str, delta: str) -> str:
        return self._encoder.encode(
            ReasoningMessageContentEvent(messageId=message_id, delta=delta)
        )

    def emit_reasoning_message_end(self, message_id: str) -> str:
        return self._encoder.encode(
            ReasoningMessageEndEvent(messageId=message_id)
        )

    def emit_reasoning_end(self, message_id: str) -> str:
        return self._encoder.encode(
            ReasoningEndEvent(messageId=message_id)
        )

    def emit_custom(self, name: str, value) -> str:
        return self._encoder.encode(CustomEvent(name=name, value=value))

    def emit_messages_snapshot(self, messages: list) -> str:
        return self._encoder.encode(
            MessagesSnapshotEvent(messages=messages)
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_core_events.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/agui_backend_demo/core/__init__.py src/agui_backend_demo/core/events.py tests/test_core_events.py
git commit -m "feat(core): add EventEmitter wrapper with all AG-UI event types"
```

---

### Task 2: Create thread store for conversation persistence

**Files:**
- Create: `src/agui_backend_demo/core/history.py`
- Test: `tests/test_core_history.py`

- [ ] **Step 1: Write tests for thread store**

```python
# tests/test_core_history.py
from agui_backend_demo.core.history import ThreadStore


def test_create_thread():
    store = ThreadStore()
    thread = store.create_thread("t1", "chat")
    assert thread["agent_type"] == "chat"
    assert thread["messages"] == []
    assert thread["events"] == []
    assert thread["state"] == {}
    assert "created_at" in thread
    assert "updated_at" in thread


def test_get_thread():
    store = ThreadStore()
    store.create_thread("t1", "chat")
    thread = store.get_thread("t1")
    assert thread is not None
    assert thread["agent_type"] == "chat"


def test_get_thread_not_found():
    store = ThreadStore()
    assert store.get_thread("nonexistent") is None


def test_list_threads_empty():
    store = ThreadStore()
    assert store.list_threads() == []


def test_list_threads():
    store = ThreadStore()
    store.create_thread("t1", "chat")
    store.create_thread("t2", "segment")
    threads = store.list_threads()
    assert len(threads) == 2
    ids = {t["id"] for t in threads}
    assert ids == {"t1", "t2"}


def test_add_message():
    store = ThreadStore()
    store.create_thread("t1", "chat")
    store.add_message("t1", {"role": "user", "content": "hello"})
    thread = store.get_thread("t1")
    assert len(thread["messages"]) == 1
    assert thread["messages"][0]["content"] == "hello"


def test_add_event():
    store = ThreadStore()
    store.create_thread("t1", "chat")
    store.add_event("t1", {"type": "RUN_STARTED"})
    thread = store.get_thread("t1")
    assert len(thread["events"]) == 1


def test_update_state():
    store = ThreadStore()
    store.create_thread("t1", "segment")
    store.update_state("t1", {"name": "Active Users"})
    thread = store.get_thread("t1")
    assert thread["state"] == {"name": "Active Users"}


def test_get_or_create_existing():
    store = ThreadStore()
    store.create_thread("t1", "chat")
    thread = store.get_or_create_thread("t1", "chat")
    assert thread["agent_type"] == "chat"


def test_get_or_create_new():
    store = ThreadStore()
    thread = store.get_or_create_thread("t1", "chat")
    assert thread["agent_type"] == "chat"
    assert store.get_thread("t1") is not None


def test_list_thread_summary_fields():
    store = ThreadStore()
    store.create_thread("t1", "chat")
    store.add_message("t1", {"role": "user", "content": "hi"})
    store.add_message("t1", {"role": "assistant", "content": "hello"})
    summaries = store.list_threads()
    s = summaries[0]
    assert s["id"] == "t1"
    assert s["agent_type"] == "chat"
    assert s["message_count"] == 2
    assert "created_at" in s
    assert "updated_at" in s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_core_history.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement thread store**

```python
# src/agui_backend_demo/core/history.py
from datetime import datetime, timezone
from typing import TypedDict


class ThreadData(TypedDict):
    messages: list[dict]
    events: list[dict]
    state: dict
    agent_type: str
    created_at: str
    updated_at: str


class ThreadStore:
    """In-memory conversation history store keyed by thread_id."""

    def __init__(self):
        self._threads: dict[str, ThreadData] = {}

    def create_thread(self, thread_id: str, agent_type: str) -> ThreadData:
        now = datetime.now(timezone.utc).isoformat()
        thread: ThreadData = {
            "messages": [],
            "events": [],
            "state": {},
            "agent_type": agent_type,
            "created_at": now,
            "updated_at": now,
        }
        self._threads[thread_id] = thread
        return thread

    def get_thread(self, thread_id: str) -> ThreadData | None:
        return self._threads.get(thread_id)

    def list_threads(self) -> list[dict]:
        return [
            {
                "id": tid,
                "agent_type": data["agent_type"],
                "message_count": len(data["messages"]),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
            }
            for tid, data in self._threads.items()
        ]

    def add_message(self, thread_id: str, message: dict) -> None:
        thread = self._threads.get(thread_id)
        if thread:
            thread["messages"].append(message)
            thread["updated_at"] = datetime.now(timezone.utc).isoformat()

    def add_event(self, thread_id: str, event: dict) -> None:
        thread = self._threads.get(thread_id)
        if thread:
            thread["events"].append(event)
            thread["updated_at"] = datetime.now(timezone.utc).isoformat()

    def update_state(self, thread_id: str, state: dict) -> None:
        thread = self._threads.get(thread_id)
        if thread:
            thread["state"] = state
            thread["updated_at"] = datetime.now(timezone.utc).isoformat()

    def get_or_create_thread(self, thread_id: str, agent_type: str) -> ThreadData:
        existing = self.get_thread(thread_id)
        if existing:
            return existing
        return self.create_thread(thread_id, agent_type)


# Module-level singleton
thread_store = ThreadStore()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_core_history.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/agui_backend_demo/core/history.py tests/test_core_history.py
git commit -m "feat(core): add ThreadStore for in-memory conversation persistence"
```

---

### Task 3: Create middleware infrastructure

**Files:**
- Create: `src/agui_backend_demo/core/middleware.py`
- Test: `tests/test_core_middleware.py`

- [ ] **Step 1: Write tests for middleware**

```python
# tests/test_core_middleware.py
import asyncio
import json

import pytest

from agui_backend_demo.core.middleware import (
    CapabilityFilterMiddleware,
    HistoryMiddleware,
    LoggingMiddleware,
)


async def _collect(stream):
    """Collect all items from an async generator."""
    items = []
    async for item in stream:
        items.append(item)
    return items


async def _mock_stream(*events):
    """Create a mock async generator of SSE-formatted events."""
    for event in events:
        yield f'data: {json.dumps(event)}\n\n'


@pytest.mark.asyncio
async def test_logging_middleware_passes_all():
    events = [
        {"type": "RUN_STARTED"},
        {"type": "TEXT_MESSAGE_CONTENT", "delta": "hi"},
        {"type": "RUN_FINISHED"},
    ]
    middleware = LoggingMiddleware()
    result = await _collect(middleware.apply(_mock_stream(*events)))
    assert len(result) == 3


@pytest.mark.asyncio
async def test_capability_filter_keeps_lifecycle():
    events = [
        {"type": "RUN_STARTED"},
        {"type": "REASONING_START"},
        {"type": "RUN_FINISHED"},
    ]
    middleware = CapabilityFilterMiddleware(allowed_types={"TEXT_MESSAGE_CONTENT"})
    result = await _collect(middleware.apply(_mock_stream(*events)))
    types = [json.loads(r.split("data: ", 1)[1].split("\n")[0])["type"] for r in result]
    assert "RUN_STARTED" in types
    assert "RUN_FINISHED" in types
    assert "REASONING_START" not in types


@pytest.mark.asyncio
async def test_capability_filter_keeps_allowed():
    events = [
        {"type": "RUN_STARTED"},
        {"type": "TEXT_MESSAGE_CONTENT", "delta": "hi"},
        {"type": "REASONING_START"},
        {"type": "RUN_FINISHED"},
    ]
    middleware = CapabilityFilterMiddleware(
        allowed_types={"TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_START", "TEXT_MESSAGE_END"}
    )
    result = await _collect(middleware.apply(_mock_stream(*events)))
    types = [json.loads(r.split("data: ", 1)[1].split("\n")[0])["type"] for r in result]
    assert "TEXT_MESSAGE_CONTENT" in types
    assert "REASONING_START" not in types


@pytest.mark.asyncio
async def test_history_middleware_stores_events():
    stored = []

    class MockStore:
        def add_event(self, thread_id, event):
            stored.append((thread_id, event))

    events = [{"type": "RUN_STARTED"}, {"type": "RUN_FINISHED"}]
    middleware = HistoryMiddleware(store=MockStore(), thread_id="t1")
    result = await _collect(middleware.apply(_mock_stream(*events)))
    assert len(result) == 2
    assert len(stored) == 2
    assert stored[0] == ("t1", {"type": "RUN_STARTED"})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_core_middleware.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement middleware**

```python
# src/agui_backend_demo/core/middleware.py
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

logger = logging.getLogger(__name__)

# Lifecycle event types that should never be filtered out
LIFECYCLE_TYPES = frozenset({
    "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR",
})


def _parse_sse_event(sse_str: str) -> dict | None:
    """Extract JSON payload from an SSE-formatted string."""
    if "data: " not in sse_str:
        return None
    try:
        json_str = sse_str.split("data: ", 1)[1].split("\n")[0]
        return json.loads(json_str)
    except (IndexError, json.JSONDecodeError):
        return None


class LoggingMiddleware:
    """Logs each event type and timestamp for debugging."""

    async def apply(self, event_stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for event_str in event_stream:
            parsed = _parse_sse_event(event_str)
            if parsed:
                logger.info("AG-UI event: %s", parsed.get("type", "UNKNOWN"))
            yield event_str


class CapabilityFilterMiddleware:
    """Filters events to only those matching allowed types. Lifecycle events always pass."""

    def __init__(self, allowed_types: set[str]):
        self._allowed = allowed_types | LIFECYCLE_TYPES

    async def apply(self, event_stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for event_str in event_stream:
            parsed = _parse_sse_event(event_str)
            if parsed is None or parsed.get("type", "") in self._allowed:
                yield event_str


class HistoryMiddleware:
    """Stores each event in a ThreadStore for serialization/history."""

    def __init__(self, store: Any, thread_id: str):
        self._store = store
        self._thread_id = thread_id

    async def apply(self, event_stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for event_str in event_stream:
            parsed = _parse_sse_event(event_str)
            if parsed:
                self._store.add_event(self._thread_id, parsed)
            yield event_str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_core_middleware.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/agui_backend_demo/core/middleware.py tests/test_core_middleware.py
git commit -m "feat(core): add logging, capability filter, and history middleware"
```

---

## Phase 2: Refactor Existing Agents into Per-Module Structure

### Task 4: Refactor segment agent into sub-package

**Files:**
- Create: `src/agui_backend_demo/agent/segment/__init__.py`
- Create: `src/agui_backend_demo/agent/segment/state.py` (move from `agent/state.py`)
- Create: `src/agui_backend_demo/agent/segment/graph.py` (move from `agent/graph.py`)
- Create: `src/agui_backend_demo/agent/segment/routes.py` (extract from `api/routes.py`)

- [ ] **Step 1: Create segment sub-package**

```python
# src/agui_backend_demo/agent/segment/__init__.py
from agui_backend_demo.agent.segment.graph import build_segment_graph

__all__ = ["build_segment_graph"]
```

- [ ] **Step 2: Move state to segment sub-package**

```python
# src/agui_backend_demo/agent/segment/state.py
from typing import TypedDict

from agui_backend_demo.schemas.segment import Segment


class SegmentAgentState(TypedDict):
    messages: list
    segment: Segment | None
    error: str | None
```

- [ ] **Step 3: Move graph to segment sub-package**

```python
# src/agui_backend_demo/agent/segment/graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.segment.state import SegmentAgentState
from agui_backend_demo.schemas.segment import Segment

SYSTEM_PROMPT = """\
You are a user segmentation expert. Given a natural language description, \
generate a structured segment definition.

## Available Field Types

- **User properties**: age, gender, country, city, language, signup_date, \
plan_type, account_status
- **Behavioral events**: purchase_count, last_purchase_date, total_spent, \
login_count, last_login_date, page_views, session_duration
- **Engagement**: email_opened, email_clicked, push_notification_opened, \
app_opens, feature_used
- **Custom attributes**: any user-defined property (use descriptive snake_case names)

## Available Operators

- **Comparison**: equals, not_equals, greater_than, less_than, \
greater_than_or_equal, less_than_or_equal
- **String**: contains, not_contains, starts_with, ends_with
- **Temporal**: within_last, before, after, between
- **Existence**: is_set, is_not_set
- **List**: in, not_in

## Rules

1. Generate a concise, descriptive segment name.
2. Write a clear human-readable description of who this segment targets.
3. Group conditions logically using AND/OR groups.
4. Use the most specific field and operator that matches the user's intent.
5. For temporal values, use clear formats like "30 days", "2024-01-01", etc.
6. If the query implies multiple independent criteria, use separate condition \
groups joined appropriately.
7. Set estimated_scope to a brief description of the expected audience size \
or reach (e.g., "Users matching all activity and location criteria").
"""


def _build_generate_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(Segment)

    async def generate_segment(state: SegmentAgentState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {"segment": result, "error": None}
        except Exception as e:
            return {"segment": None, "error": str(e)}

    return generate_segment


def build_segment_graph(model: str = "claude-sonnet-4-20250514"):
    """Build and compile the segment generation graph."""
    llm = ChatAnthropic(model=model)

    graph = StateGraph(SegmentAgentState)
    graph.add_node("generate_segment", _build_generate_node(llm))
    graph.add_edge(START, "generate_segment")
    graph.add_edge("generate_segment", END)

    return graph.compile()
```

- [ ] **Step 4: Create segment routes**

```python
# src/agui_backend_demo/agent/segment/routes.py
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

    thread_store.get_or_create_thread(thread_id, "segment")
    thread_store.add_message(thread_id, {"role": "user", "content": query})

    async def event_stream():
        message_id = str(uuid.uuid4())

        yield emitter.emit_run_started(thread_id, run_id)
        yield emitter.emit_step_start("generate_segment")

        try:
            result = await segment_graph.ainvoke(
                {"messages": [HumanMessage(content=query)], "segment": None, "error": None}
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
```

- [ ] **Step 5: Run lint check**

Run: `uv run ruff check src/agui_backend_demo/agent/segment/`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add src/agui_backend_demo/agent/segment/
git commit -m "refactor(segment): move segment agent into self-contained sub-package"
```

---

### Task 5: Refactor chat agent into sub-package

**Files:**
- Create: `src/agui_backend_demo/agent/chat/__init__.py`
- Create: `src/agui_backend_demo/agent/chat/graph.py` (move from `agent/chat_agent.py`)
- Create: `src/agui_backend_demo/agent/chat/routes.py` (extract from `api/routes.py`)

- [ ] **Step 1: Create chat sub-package**

```python
# src/agui_backend_demo/agent/chat/__init__.py
from agui_backend_demo.agent.chat.graph import build_chat_agent

__all__ = ["build_chat_agent"]
```

- [ ] **Step 2: Move graph to chat sub-package**

```python
# src/agui_backend_demo/agent/chat/graph.py
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = """\
You are a friendly, helpful AI assistant for an email marketing platform. \
You can help with segment generation, template creation, campaign building, \
and custom property generation. Answer clearly and concisely. \
If you don't know something, say so honestly.\
"""


def build_chat_agent(model: str = "claude-sonnet-4-20250514"):
    """Build a generic chat agent using create_react_agent."""
    llm = ChatAnthropic(model=model)
    return create_react_agent(llm, tools=[], prompt=SYSTEM_PROMPT)
```

- [ ] **Step 3: Create chat routes**

```python
# src/agui_backend_demo/agent/chat/routes.py
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from agui_backend_demo.core.events import EventEmitter, extract_user_query, get_field
from agui_backend_demo.core.history import thread_store
from agui_backend_demo.core.middleware import HistoryMiddleware, LoggingMiddleware

router = APIRouter(prefix="/api/v1")
emitter = EventEmitter()


@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    user_message = extract_user_query(body.get("messages", []))

    chat_agent = request.app.state.chat_agent

    thread_store.get_or_create_thread(thread_id, "chat")
    thread_store.add_message(thread_id, {"role": "user", "content": user_message})

    async def event_stream():
        message_id = str(uuid.uuid4())
        message_started = False
        full_response = ""

        yield emitter.emit_run_started(thread_id, run_id)

        try:
            async for event in chat_agent.astream_events(
                {"messages": [{"role": "user", "content": user_message}]},
                config={"configurable": {"thread_id": thread_id}},
                version="v2",
            ):
                if (
                    event["event"] == "on_chat_model_stream"
                    and event["data"]["chunk"].content
                ):
                    content = event["data"]["chunk"].content

                    text = ""
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block["text"]
                                break
                    elif isinstance(content, str):
                        text = content

                    if not text:
                        continue

                    if not message_started:
                        yield emitter.emit_text_start(message_id, "assistant")
                        message_started = True

                    yield emitter.emit_text_content(message_id, text)
                    full_response += text

            if message_started:
                yield emitter.emit_text_end(message_id)
                thread_store.add_message(
                    thread_id, {"role": "assistant", "content": full_response}
                )

        except Exception as e:
            logging.exception("Chat agent error")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    stream = LoggingMiddleware().apply(
        HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
    )

    return StreamingResponse(stream, media_type=emitter.content_type)
```

- [ ] **Step 4: Commit**

```bash
git add src/agui_backend_demo/agent/chat/
git commit -m "refactor(chat): move chat agent into self-contained sub-package"
```

---

### Task 6: Update main.py and clean up old files

**Files:**
- Modify: `src/agui_backend_demo/main.py`
- Delete: `src/agui_backend_demo/api/routes.py`
- Delete: `src/agui_backend_demo/agent/graph.py`
- Delete: `src/agui_backend_demo/agent/state.py`
- Delete: `src/agui_backend_demo/agent/chat_agent.py`

- [ ] **Step 1: Update main.py**

Replace the entire contents of `src/agui_backend_demo/main.py` with:

```python
# src/agui_backend_demo/main.py
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agui_backend_demo.agent.chat.graph import build_chat_agent
from agui_backend_demo.agent.segment.graph import build_segment_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Building agents...")
    app.state.segment_graph = build_segment_graph()
    app.state.chat_agent = build_chat_agent()
    logger.info("Agents ready")
    yield


app = FastAPI(
    title="AG-UI Core Concepts Demo",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register agent routers
from agui_backend_demo.agent.chat.routes import router as chat_router
from agui_backend_demo.agent.segment.routes import router as segment_router

app.include_router(segment_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "agui_backend_demo.main:app", host="0.0.0.0", port=8000, reload=True
    )
```

- [ ] **Step 2: Delete old files**

```bash
rm src/agui_backend_demo/api/routes.py
rm src/agui_backend_demo/agent/graph.py
rm src/agui_backend_demo/agent/state.py
rm src/agui_backend_demo/agent/chat_agent.py
```

- [ ] **Step 3: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All existing tests PASS

- [ ] **Step 4: Run lint check**

Run: `uv run ruff check src/`
Expected: No errors (may need to fix unused imports in `agent/__init__.py`)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: update main.py to use per-module routers, delete old files"
```

---

## Phase 3: New Schemas, Thread API, and Capabilities

### Task 7: Create new Pydantic schemas

**Files:**
- Create: `src/agui_backend_demo/schemas/template.py`
- Create: `src/agui_backend_demo/schemas/campaign.py`
- Create: `src/agui_backend_demo/schemas/custom_property.py`
- Test: `tests/test_schemas_new.py`

- [ ] **Step 1: Write tests for new schemas**

```python
# tests/test_schemas_new.py
from agui_backend_demo.schemas.template import EmailTemplate, TemplateSection
from agui_backend_demo.schemas.campaign import Campaign
from agui_backend_demo.schemas.custom_property import CustomProperty


def test_template_section_creation():
    section = TemplateSection(id="s1", type="header", content="<h1>Hello</h1>")
    assert section.id == "s1"
    assert section.type == "header"
    assert section.styles == {}


def test_template_section_with_styles():
    section = TemplateSection(
        id="s1", type="body", content="<p>Hi</p>",
        styles={"background": "#fff", "padding": "20px"},
    )
    assert section.styles["background"] == "#fff"


def test_email_template_defaults():
    template = EmailTemplate()
    assert template.html == ""
    assert template.css == ""
    assert template.subject == ""
    assert template.preview_text == ""
    assert template.sections == []
    assert template.version == 1


def test_email_template_full():
    template = EmailTemplate(
        html="<html><body>Hi</body></html>",
        css="body { margin: 0; }",
        subject="Welcome!",
        preview_text="Welcome to our platform",
        sections=[
            TemplateSection(id="h1", type="header", content="<h1>Welcome</h1>"),
            TemplateSection(id="b1", type="body", content="<p>Content</p>"),
        ],
        version=2,
    )
    assert len(template.sections) == 2
    assert template.version == 2


def test_email_template_roundtrip():
    template = EmailTemplate(
        subject="Test", sections=[
            TemplateSection(id="s1", type="header", content="<h1>Hi</h1>"),
        ]
    )
    json_str = template.model_dump_json()
    restored = EmailTemplate.model_validate_json(json_str)
    assert restored == template


def test_campaign_defaults():
    campaign = Campaign(name="Test Campaign")
    assert campaign.segment_id is None
    assert campaign.template_id is None
    assert campaign.status == "draft"


def test_campaign_full():
    campaign = Campaign(
        name="Spring Sale",
        segment_id="seg-1",
        template_id="tmpl-1",
        subject="Spring Sale - 50% Off!",
        send_time="2026-04-01T10:00:00Z",
        status="scheduled",
    )
    assert campaign.status == "scheduled"


def test_campaign_roundtrip():
    campaign = Campaign(name="Test")
    json_str = campaign.model_dump_json()
    restored = Campaign.model_validate_json(json_str)
    assert restored == campaign


def test_custom_property_creation():
    prop = CustomProperty(
        name="days_since_signup",
        description="Number of days since user signed up",
        javascript_code="return Math.floor((Date.now() - new Date(user.signup_date)) / 86400000);",
    )
    assert prop.property_type == "string"
    assert prop.example_value is None


def test_custom_property_full():
    prop = CustomProperty(
        name="is_power_user",
        description="True if user has logged in 30+ times",
        javascript_code="return user.login_count >= 30;",
        property_type="boolean",
        example_value="true",
    )
    assert prop.property_type == "boolean"


def test_custom_property_roundtrip():
    prop = CustomProperty(
        name="test", description="test", javascript_code="return 1;"
    )
    json_str = prop.model_dump_json()
    restored = CustomProperty.model_validate_json(json_str)
    assert restored == prop
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_schemas_new.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement schemas**

```python
# src/agui_backend_demo/schemas/template.py
from pydantic import BaseModel


class TemplateSection(BaseModel):
    """A section within an email template."""

    id: str
    type: str  # header, body, footer, cta, image
    content: str
    styles: dict[str, str] = {}


class EmailTemplate(BaseModel):
    """An email template definition."""

    html: str = ""
    css: str = ""
    subject: str = ""
    preview_text: str = ""
    sections: list[TemplateSection] = []
    version: int = 1
```

```python
# src/agui_backend_demo/schemas/campaign.py
from pydantic import BaseModel


class Campaign(BaseModel):
    """An email campaign definition."""

    name: str
    segment_id: str | None = None
    template_id: str | None = None
    subject: str = ""
    send_time: str | None = None
    status: str = "draft"
```

```python
# src/agui_backend_demo/schemas/custom_property.py
from pydantic import BaseModel


class CustomProperty(BaseModel):
    """A custom user property with JavaScript computation code."""

    name: str
    description: str
    javascript_code: str
    property_type: str = "string"  # string, number, boolean, date
    example_value: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_schemas_new.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/agui_backend_demo/schemas/template.py src/agui_backend_demo/schemas/campaign.py src/agui_backend_demo/schemas/custom_property.py tests/test_schemas_new.py
git commit -m "feat(schemas): add EmailTemplate, Campaign, and CustomProperty schemas"
```

---

### Task 8: Create thread history and capabilities API endpoints

**Files:**
- Create: `src/agui_backend_demo/api/threads.py`
- Create: `src/agui_backend_demo/api/capabilities.py`
- Modify: `src/agui_backend_demo/main.py`
- Test: `tests/test_threads_api.py`

- [ ] **Step 1: Write tests for thread API**

```python
# tests/test_threads_api.py
import pytest
from fastapi.testclient import TestClient

from agui_backend_demo.core.history import thread_store
from agui_backend_demo.main import app


@pytest.fixture(autouse=True)
def clear_store():
    """Clear thread store before each test."""
    thread_store._threads.clear()
    yield
    thread_store._threads.clear()


client = TestClient(app)


def test_list_threads_empty():
    response = client.get("/api/v1/threads")
    assert response.status_code == 200
    assert response.json() == []


def test_list_threads_with_data():
    thread_store.create_thread("t1", "chat")
    thread_store.add_message("t1", {"role": "user", "content": "hi"})
    response = client.get("/api/v1/threads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "t1"
    assert data[0]["message_count"] == 1


def test_get_thread():
    thread_store.create_thread("t1", "segment")
    thread_store.add_message("t1", {"role": "user", "content": "hi"})
    response = client.get("/api/v1/threads/t1")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "segment"
    assert len(data["messages"]) == 1


def test_get_thread_not_found():
    response = client.get("/api/v1/threads/nonexistent")
    assert response.status_code == 404


def test_get_thread_messages():
    thread_store.create_thread("t1", "chat")
    thread_store.add_message("t1", {"role": "user", "content": "hi"})
    thread_store.add_message("t1", {"role": "assistant", "content": "hello"})
    response = client.get("/api/v1/threads/t1/messages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["role"] == "user"
    assert data[1]["role"] == "assistant"


def test_get_thread_messages_not_found():
    response = client.get("/api/v1/threads/nonexistent/messages")
    assert response.status_code == 404


def test_capabilities_endpoint():
    response = client.get("/api/v1/agents/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "segment" in data
    assert "chat" in data
    assert data["segment"]["streaming"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_threads_api.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement thread API**

```python
# src/agui_backend_demo/api/threads.py
from fastapi import APIRouter, HTTPException

from agui_backend_demo.core.history import thread_store

router = APIRouter(prefix="/api/v1")


@router.get("/threads")
async def list_threads():
    return thread_store.list_threads()


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    thread = thread_store.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str):
    thread = thread_store.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread["messages"]
```

- [ ] **Step 4: Implement capabilities API**

```python
# src/agui_backend_demo/api/capabilities.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

AGENT_CAPABILITIES = {
    "segment": {
        "streaming": True,
        "state": True,
        "tools": False,
        "reasoning": False,
        "activity": False,
        "human_in_loop": False,
    },
    "template": {
        "streaming": True,
        "state": True,
        "tools": True,
        "reasoning": True,
        "activity": True,
        "human_in_loop": True,
    },
    "chat": {
        "streaming": True,
        "state": False,
        "tools": True,
        "reasoning": False,
        "activity": False,
        "multi_agent": True,
    },
    "campaign": {
        "streaming": True,
        "state": True,
        "tools": False,
        "reasoning": False,
        "activity": False,
    },
    "custom_property": {
        "streaming": True,
        "state": True,
        "tools": False,
        "reasoning": False,
        "custom_events": True,
    },
}


@router.get("/agents/capabilities")
async def get_capabilities():
    return AGENT_CAPABILITIES
```

- [ ] **Step 5: Register routers in main.py**

Add these imports and registrations to `main.py` after the existing router registrations:

```python
from agui_backend_demo.api.threads import router as threads_router
from agui_backend_demo.api.capabilities import router as capabilities_router

app.include_router(threads_router)
app.include_router(capabilities_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_threads_api.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/agui_backend_demo/api/threads.py src/agui_backend_demo/api/capabilities.py src/agui_backend_demo/main.py tests/test_threads_api.py
git commit -m "feat(api): add thread history and capabilities endpoints"
```

---

## Phase 4: Template Creator Agent (Full Depth)

### Task 9: Create template agent backend

**Files:**
- Create: `src/agui_backend_demo/agent/template/__init__.py`
- Create: `src/agui_backend_demo/agent/template/state.py`
- Create: `src/agui_backend_demo/agent/template/tools.py`
- Create: `src/agui_backend_demo/agent/template/graph.py`
- Create: `src/agui_backend_demo/agent/template/routes.py`
- Modify: `src/agui_backend_demo/main.py`
- Test: `tests/test_template_agent.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_template_agent.py
from agui_backend_demo.agent.template.state import TemplateAgentState
from agui_backend_demo.agent.template.tools import get_frontend_tool_schemas
from agui_backend_demo.schemas.template import EmailTemplate


def test_template_agent_state_structure():
    state: TemplateAgentState = {
        "messages": [],
        "template": None,
        "error": None,
        "version": 0,
    }
    assert state["version"] == 0


def test_frontend_tool_schemas():
    tools = get_frontend_tool_schemas()
    assert len(tools) == 3
    names = {t["name"] for t in tools}
    assert names == {"update_section", "add_section", "remove_section"}
    for tool in tools:
        assert "description" in tool
        assert "parameters" in tool


def test_email_template_to_state():
    template = EmailTemplate(subject="Hello", html="<h1>Hi</h1>")
    state_dict = template.model_dump()
    assert state_dict["subject"] == "Hello"
    assert state_dict["version"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_template_agent.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Create template package init**

```python
# src/agui_backend_demo/agent/template/__init__.py
from agui_backend_demo.agent.template.graph import build_template_graph

__all__ = ["build_template_graph"]
```

- [ ] **Step 4: Create template state**

```python
# src/agui_backend_demo/agent/template/state.py
from typing import TypedDict


class TemplateAgentState(TypedDict):
    messages: list
    template: dict | None
    error: str | None
    version: int
```

- [ ] **Step 5: Create frontend tool schemas**

```python
# src/agui_backend_demo/agent/template/tools.py

FRONTEND_TOOLS = [
    {
        "name": "update_section",
        "description": "Update the content of an existing template section",
        "parameters": {
            "type": "object",
            "properties": {
                "section_id": {
                    "type": "string",
                    "description": "The ID of the section to update",
                },
                "content": {
                    "type": "string",
                    "description": "The new HTML content for the section",
                },
            },
            "required": ["section_id", "content"],
        },
    },
    {
        "name": "add_section",
        "description": "Add a new section to the email template",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Section type: header, body, footer, cta, or image",
                },
                "content": {
                    "type": "string",
                    "description": "The HTML content for the new section",
                },
                "position": {
                    "type": "integer",
                    "description": "Position index to insert at (0-based)",
                },
            },
            "required": ["type", "content"],
        },
    },
    {
        "name": "remove_section",
        "description": "Remove a section from the email template",
        "parameters": {
            "type": "object",
            "properties": {
                "section_id": {
                    "type": "string",
                    "description": "The ID of the section to remove",
                },
            },
            "required": ["section_id"],
        },
    },
]


def get_frontend_tool_schemas() -> list[dict]:
    """Return the list of frontend-defined tool schemas."""
    return FRONTEND_TOOLS
```

- [ ] **Step 6: Create template graph**

```python
# src/agui_backend_demo/agent/template/graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.template.state import TemplateAgentState
from agui_backend_demo.schemas.template import EmailTemplate

SYSTEM_PROMPT = """\
You are an email template design expert. Generate professional HTML email \
templates based on user descriptions.

When generating a template, create:
1. A clear subject line
2. Preview text (the snippet shown in inbox)
3. Well-structured HTML with sections (header, body, footer, CTA)
4. Inline CSS for email client compatibility
5. Responsive design considerations

Use a 600px centered layout, table-based structure for email compatibility. \
Include placeholder content that demonstrates the template's purpose.

Return a complete EmailTemplate with sections broken into logical parts.
"""

MODIFY_PROMPT = """\
You are an email template design expert. The user wants to modify an existing \
template. Here is the current template:

Subject: {subject}
HTML: {html}

Apply the user's requested changes and return the updated template. \
Preserve the overall structure unless the user asks to change it.
"""


def _build_generate_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(EmailTemplate)

    async def generate_template(state: TemplateAgentState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {"template": result.model_dump(), "error": None, "version": 1}
        except Exception as e:
            return {"template": None, "error": str(e)}

    return generate_template


def _build_modify_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(EmailTemplate)

    async def modify_template(state: TemplateAgentState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

            current = state.get("template", {})
            prompt = MODIFY_PROMPT.format(
                subject=current.get("subject", ""),
                html=current.get("html", ""),
            )
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {
                "template": result.model_dump(),
                "error": None,
                "version": state.get("version", 0) + 1,
            }
        except Exception as e:
            return {"template": None, "error": str(e)}

    return modify_template


def _route_by_state(state: TemplateAgentState) -> str:
    if state.get("template") is None:
        return "generate_template"
    return "modify_template"


def build_template_graph(model: str = "claude-sonnet-4-20250514"):
    """Build and compile the template generation/modification graph."""
    llm = ChatAnthropic(model=model)

    graph = StateGraph(TemplateAgentState)
    graph.add_node("generate_template", _build_generate_node(llm))
    graph.add_node("modify_template", _build_modify_node(llm))
    graph.add_conditional_edges(START, _route_by_state)
    graph.add_edge("generate_template", END)
    graph.add_edge("modify_template", END)

    return graph.compile()
```

- [ ] **Step 7: Create template routes with all AG-UI events**

```python
# src/agui_backend_demo/agent/template/routes.py
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

# Mock reasoning content for demonstrating the reasoning event pattern
REASONING_STEPS = [
    "Analyzing the user's request for an email template...",
    "Considering email client compatibility requirements...",
    "Planning section layout: header, body, CTA, footer...",
    "Selecting responsive design approach with 600px container...",
]

# Mock activity stages for demonstrating activity events
ACTIVITY_STAGES = [
    {"title": "Analyzing template structure", "progress": 0.2, "details": "Understanding requirements..."},
    {"title": "Generating section content", "progress": 0.5, "details": "Creating HTML sections..."},
    {"title": "Applying responsive styles", "progress": 0.8, "details": "Adding inline CSS..."},
    {"title": "Finalizing template", "progress": 1.0, "details": "Template ready"},
]


def _compute_json_patch(old: dict, new: dict) -> list[dict]:
    """Compute a simple JSON Patch (RFC 6902) between two dicts."""
    ops = []
    all_keys = set(list(old.keys()) + list(new.keys()))
    for key in all_keys:
        path = f"/{key}"
        if key not in old:
            ops.append({"op": "add", "path": path, "value": new[key]})
        elif key not in new:
            ops.append({"op": "remove", "path": path})
        elif old[key] != new[key]:
            ops.append({"op": "replace", "path": path, "value": new[key]})
    return ops


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

    existing_template = frontend_state or thread["state"].get("template")

    async def event_stream():
        message_id = str(uuid.uuid4())
        reasoning_id = str(uuid.uuid4())
        activity_id = str(uuid.uuid4())

        yield emitter.emit_run_started(thread_id, run_id)
        yield emitter.emit_step_start("template_processing")

        # --- Reasoning Events (demonstrating chain-of-thought) ---
        yield emitter.emit_reasoning_start(reasoning_id)
        yield emitter.emit_reasoning_message_start(reasoning_id)
        for step in REASONING_STEPS:
            yield emitter.emit_reasoning_content(reasoning_id, step + " ")
            await asyncio.sleep(0.1)
        yield emitter.emit_reasoning_message_end(reasoning_id)
        yield emitter.emit_reasoning_end(reasoning_id)

        # --- Activity Events (demonstrating progress tracking) ---
        for stage in ACTIVITY_STAGES:
            yield emitter.emit_activity_snapshot(
                activity_id, "processing", stage
            )
            await asyncio.sleep(0.1)

        try:
            graph_input: dict = {
                "messages": [HumanMessage(content=query)],
                "template": existing_template,
                "error": None,
                "version": existing_template.get("version", 0) if existing_template else 0,
            }

            result = await template_graph.ainvoke(graph_input)

            if result.get("error"):
                yield emitter.emit_run_error(result["error"])
                return

            new_template = result["template"]

            # --- State Events ---
            if existing_template is None:
                # First generation: full snapshot
                yield emitter.emit_state_snapshot(new_template)
            else:
                # Modification: emit delta (JSON Patch)
                patch = _compute_json_patch(existing_template, new_template)
                if patch:
                    yield emitter.emit_state_delta(patch)
                yield emitter.emit_state_snapshot(new_template)

            thread_store.update_state(thread_id, {"template": new_template})

            # --- Tool Call Events (demonstrating FE-defined tools) ---
            sections = new_template.get("sections", [])
            if sections:
                tool_call_id = str(uuid.uuid4())
                yield emitter.emit_tool_call_start(
                    tool_call_id, "update_section", message_id
                )
                yield emitter.emit_tool_call_args(
                    tool_call_id,
                    json.dumps({"section_id": sections[0].get("id", "s1"), "content": sections[0].get("content", "")}),
                )
                yield emitter.emit_tool_call_end(tool_call_id)

            # --- Text Message ---
            action = "Updated" if existing_template else "Created"
            subject = new_template.get("subject", "Untitled")
            section_count = len(sections)
            summary = (
                f"{action} template: **{subject}**\n\n"
                f"{section_count} section(s) generated. "
                f"You can edit the template in the left panel."
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
```

- [ ] **Step 8: Register template agent in main.py**

Add to `main.py` lifespan:
```python
from agui_backend_demo.agent.template.graph import build_template_graph
# Inside lifespan:
app.state.template_graph = build_template_graph()
```

Add router registration:
```python
from agui_backend_demo.agent.template.routes import router as template_router
app.include_router(template_router)
```

- [ ] **Step 9: Run tests**

Run: `uv run pytest tests/test_template_agent.py -v`
Expected: All PASS

- [ ] **Step 10: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 11: Commit**

```bash
git add src/agui_backend_demo/agent/template/ src/agui_backend_demo/main.py tests/test_template_agent.py
git commit -m "feat(template): add Template Creator agent with state deltas, reasoning, activity, and tool call events"
```

---

## Phase 5: Stub Agents (Campaign Builder & Custom Property Generator)

### Task 10: Create campaign builder stub

**Files:**
- Create: `src/agui_backend_demo/agent/campaign/__init__.py`
- Create: `src/agui_backend_demo/agent/campaign/state.py`
- Create: `src/agui_backend_demo/agent/campaign/graph.py`
- Create: `src/agui_backend_demo/agent/campaign/routes.py`
- Modify: `src/agui_backend_demo/main.py`

- [ ] **Step 1: Create campaign package**

```python
# src/agui_backend_demo/agent/campaign/__init__.py
from agui_backend_demo.agent.campaign.graph import build_campaign_graph

__all__ = ["build_campaign_graph"]
```

```python
# src/agui_backend_demo/agent/campaign/state.py
from typing import TypedDict


class CampaignState(TypedDict):
    messages: list
    campaign: dict | None
    segment: dict | None
    template: dict | None
    error: str | None
```

- [ ] **Step 2: Create campaign graph**

```python
# src/agui_backend_demo/agent/campaign/graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.campaign.state import CampaignState
from agui_backend_demo.schemas.campaign import Campaign

SYSTEM_PROMPT = """\
You are an email campaign builder. Given a description, generate a campaign \
definition with name, subject line, and status. This is a stub implementation \
demonstrating multi-agent state composition in AG-UI.
"""


def _build_generate_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(Campaign)

    async def generate_campaign(state: CampaignState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {"campaign": result.model_dump(), "error": None}
        except Exception as e:
            return {"campaign": None, "error": str(e)}

    return generate_campaign


def build_campaign_graph(model: str = "claude-sonnet-4-20250514"):
    """Build and compile the campaign generation graph."""
    llm = ChatAnthropic(model=model)

    graph = StateGraph(CampaignState)
    graph.add_node("generate_campaign", _build_generate_node(llm))
    graph.add_edge(START, "generate_campaign")
    graph.add_edge("generate_campaign", END)

    return graph.compile()
```

- [ ] **Step 3: Create campaign routes**

```python
# src/agui_backend_demo/agent/campaign/routes.py
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

    thread_store.get_or_create_thread(thread_id, "campaign")
    thread_store.add_message(thread_id, {"role": "user", "content": query})

    async def event_stream():
        message_id = str(uuid.uuid4())

        yield emitter.emit_run_started(thread_id, run_id)
        yield emitter.emit_step_start("generate_campaign")

        try:
            result = await campaign_graph.ainvoke(
                {"messages": [HumanMessage(content=query)], "campaign": None, "segment": None, "template": None, "error": None}
            )

            if result.get("error"):
                yield emitter.emit_run_error(result["error"])
                return

            campaign = result["campaign"]
            thread_store.update_state(thread_id, {"campaign": campaign})

            yield emitter.emit_state_snapshot(campaign)

            summary = f"Created campaign: **{campaign.get('name', 'Untitled')}**\n\nStatus: {campaign.get('status', 'draft')}"
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
```

- [ ] **Step 4: Register campaign agent in main.py**

Add to lifespan:
```python
from agui_backend_demo.agent.campaign.graph import build_campaign_graph
# Inside lifespan:
app.state.campaign_graph = build_campaign_graph()
```

Add router:
```python
from agui_backend_demo.agent.campaign.routes import router as campaign_router
app.include_router(campaign_router)
```

- [ ] **Step 5: Commit**

```bash
git add src/agui_backend_demo/agent/campaign/ src/agui_backend_demo/main.py
git commit -m "feat(campaign): add Campaign Builder stub agent with state snapshots"
```

---

### Task 11: Create custom property generator stub

**Files:**
- Create: `src/agui_backend_demo/agent/custom_property/__init__.py`
- Create: `src/agui_backend_demo/agent/custom_property/state.py`
- Create: `src/agui_backend_demo/agent/custom_property/graph.py`
- Create: `src/agui_backend_demo/agent/custom_property/routes.py`
- Modify: `src/agui_backend_demo/main.py`

- [ ] **Step 1: Create custom property package**

```python
# src/agui_backend_demo/agent/custom_property/__init__.py
from agui_backend_demo.agent.custom_property.graph import build_custom_property_graph

__all__ = ["build_custom_property_graph"]
```

```python
# src/agui_backend_demo/agent/custom_property/state.py
from typing import TypedDict


class CustomPropertyState(TypedDict):
    messages: list
    custom_property: dict | None
    error: str | None
```

- [ ] **Step 2: Create custom property graph**

```python
# src/agui_backend_demo/agent/custom_property/graph.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agui_backend_demo.agent.custom_property.state import CustomPropertyState
from agui_backend_demo.schemas.custom_property import CustomProperty

SYSTEM_PROMPT = """\
You are a custom property generator for an email marketing platform. \
Given a description, generate a custom user property definition with:
1. A snake_case property name
2. A clear description
3. JavaScript code that computes the property value from a user object
4. The property type (string, number, boolean, or date)
5. An example value

The JavaScript code should be a function body that has access to a `user` \
object with fields like: signup_date, login_count, purchase_count, \
total_spent, last_login_date, email_opened, country, plan_type.
"""


def _build_generate_node(llm: ChatAnthropic):
    structured_llm = llm.with_structured_output(CustomProperty)

    async def generate_property(state: CustomPropertyState) -> dict:
        try:
            query = ""
            for msg in reversed(state["messages"]):
                if hasattr(msg, "content"):
                    query = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=query),
            ]
            result = await structured_llm.ainvoke(messages)
            return {"custom_property": result.model_dump(), "error": None}
        except Exception as e:
            return {"custom_property": None, "error": str(e)}

    return generate_property


def build_custom_property_graph(model: str = "claude-sonnet-4-20250514"):
    """Build and compile the custom property generation graph."""
    llm = ChatAnthropic(model=model)

    graph = StateGraph(CustomPropertyState)
    graph.add_node("generate_property", _build_generate_node(llm))
    graph.add_edge(START, "generate_property")
    graph.add_edge("generate_property", END)

    return graph.compile()
```

- [ ] **Step 3: Create custom property routes with custom events**

```python
# src/agui_backend_demo/agent/custom_property/routes.py
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


@router.post("/custom-property")
async def handle_custom_property(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    query = extract_user_query(body.get("messages", []))

    custom_property_graph = request.app.state.custom_property_graph

    thread_store.get_or_create_thread(thread_id, "custom_property")
    thread_store.add_message(thread_id, {"role": "user", "content": query})

    async def event_stream():
        message_id = str(uuid.uuid4())

        yield emitter.emit_run_started(thread_id, run_id)
        yield emitter.emit_step_start("generate_property")

        try:
            result = await custom_property_graph.ainvoke(
                {"messages": [HumanMessage(content=query)], "custom_property": None, "error": None}
            )

            if result.get("error"):
                yield emitter.emit_run_error(result["error"])
                return

            prop = result["custom_property"]
            thread_store.update_state(thread_id, {"custom_property": prop})

            # --- Custom Event (demonstrating AG-UI custom events) ---
            yield emitter.emit_custom("property_generated", {
                "property_name": prop.get("name", ""),
                "property_type": prop.get("property_type", "string"),
                "has_code": bool(prop.get("javascript_code")),
            })

            yield emitter.emit_state_snapshot(prop)

            summary = (
                f"Generated custom property: **{prop.get('name', 'unnamed')}**\n\n"
                f"Type: `{prop.get('property_type', 'string')}`\n\n"
                f"{prop.get('description', '')}"
            )
            yield emitter.emit_text_start(message_id, "assistant")
            yield emitter.emit_text_content(message_id, summary)
            yield emitter.emit_text_end(message_id)

            thread_store.add_message(
                thread_id, {"role": "assistant", "content": summary}
            )

        except Exception as e:
            logging.exception("Custom property generation failed")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_step_finish("generate_property")
        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    stream = LoggingMiddleware().apply(
        HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
    )

    return StreamingResponse(stream, media_type=emitter.content_type)
```

- [ ] **Step 4: Register custom property agent in main.py**

Add to lifespan:
```python
from agui_backend_demo.agent.custom_property.graph import build_custom_property_graph
# Inside lifespan:
app.state.custom_property_graph = build_custom_property_graph()
```

Add router:
```python
from agui_backend_demo.agent.custom_property.routes import router as custom_property_router
app.include_router(custom_property_router)
```

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/agui_backend_demo/agent/custom_property/ src/agui_backend_demo/main.py
git commit -m "feat(custom-property): add Custom Property Generator stub with custom events"
```

---

## Phase 6: Extend Chat Agent with Backend Tools

### Task 12: Add backend tools and multi-agent orchestration to chat

**Files:**
- Create: `src/agui_backend_demo/agent/chat/tools.py`
- Modify: `src/agui_backend_demo/agent/chat/graph.py`
- Modify: `src/agui_backend_demo/agent/chat/routes.py`

- [ ] **Step 1: Create chat backend tools**

```python
# src/agui_backend_demo/agent/chat/tools.py
import json

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from agui_backend_demo.schemas.campaign import Campaign
from agui_backend_demo.schemas.custom_property import CustomProperty
from agui_backend_demo.schemas.segment import Segment


@tool
async def generate_segment(description: str) -> str:
    """Generate a user segment based on a description. Use this when the user
    wants to create audience segments for targeting."""
    from agui_backend_demo.agent.segment.graph import build_segment_graph

    graph = build_segment_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=description)], "segment": None, "error": None}
    )
    if result.get("error"):
        return json.dumps({"error": result["error"]})
    return result["segment"].model_dump_json()


@tool
async def create_template(brief: str) -> str:
    """Create an email template based on a brief. Use this when the user
    wants to create or design an email template."""
    from agui_backend_demo.agent.template.graph import build_template_graph

    graph = build_template_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=brief)], "template": None, "error": None, "version": 0}
    )
    if result.get("error"):
        return json.dumps({"error": result["error"]})
    return json.dumps(result["template"])


@tool
async def generate_custom_property(description: str) -> str:
    """Generate a custom user property with JavaScript code. Use this when the
    user wants to create computed properties for segmentation."""
    from agui_backend_demo.agent.custom_property.graph import build_custom_property_graph

    graph = build_custom_property_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=description)], "custom_property": None, "error": None}
    )
    if result.get("error"):
        return json.dumps({"error": result["error"]})
    return json.dumps(result["custom_property"])
```

- [ ] **Step 2: Update chat graph to use tools**

Replace `src/agui_backend_demo/agent/chat/graph.py` with:

```python
# src/agui_backend_demo/agent/chat/graph.py
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from agui_backend_demo.agent.chat.tools import (
    create_template,
    generate_custom_property,
    generate_segment,
)

SYSTEM_PROMPT = """\
You are a helpful AI assistant for an email marketing platform. You have access \
to specialized tools for:

1. **Segment Generation** - Create audience segments with targeting conditions
2. **Template Creation** - Design professional HTML email templates
3. **Custom Properties** - Generate computed user properties with JavaScript code

Use these tools when the user's request matches their purpose. For general \
questions, answer directly without tools. Be concise and helpful.\
"""


def build_chat_agent(model: str = "claude-sonnet-4-20250514"):
    """Build a chat agent with multi-agent orchestration tools."""
    llm = ChatAnthropic(model=model)
    return create_react_agent(
        llm,
        tools=[generate_segment, create_template, generate_custom_property],
        prompt=SYSTEM_PROMPT,
    )
```

- [ ] **Step 3: Update chat routes for tool call event streaming**

Replace `src/agui_backend_demo/agent/chat/routes.py` with:

```python
# src/agui_backend_demo/agent/chat/routes.py
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from agui_backend_demo.core.events import EventEmitter, extract_user_query, get_field
from agui_backend_demo.core.history import thread_store
from agui_backend_demo.core.middleware import (
    CapabilityFilterMiddleware,
    HistoryMiddleware,
    LoggingMiddleware,
)

router = APIRouter(prefix="/api/v1")
emitter = EventEmitter()


@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    thread_id = get_field(body, "thread_id", "threadId", str(uuid.uuid4()))
    run_id = get_field(body, "run_id", "runId", str(uuid.uuid4()))
    user_message = extract_user_query(body.get("messages", []))

    chat_agent = request.app.state.chat_agent

    thread_store.get_or_create_thread(thread_id, "chat")
    thread_store.add_message(thread_id, {"role": "user", "content": user_message})

    async def event_stream():
        message_id = str(uuid.uuid4())
        message_started = False
        full_response = ""
        active_tool_calls = {}

        yield emitter.emit_run_started(thread_id, run_id)

        try:
            async for event in chat_agent.astream_events(
                {"messages": [{"role": "user", "content": user_message}]},
                config={"configurable": {"thread_id": thread_id}},
                version="v2",
            ):
                event_name = event.get("event", "")

                # Handle tool call events (backend tools)
                if event_name == "on_tool_start":
                    tool_call_id = str(uuid.uuid4())
                    tool_name = event.get("name", "unknown")
                    active_tool_calls[event.get("run_id", "")] = tool_call_id
                    yield emitter.emit_tool_call_start(
                        tool_call_id, tool_name, message_id
                    )
                    tool_input = event.get("data", {}).get("input", "")
                    if isinstance(tool_input, dict):
                        import json
                        yield emitter.emit_tool_call_args(
                            tool_call_id, json.dumps(tool_input)
                        )
                    elif isinstance(tool_input, str):
                        yield emitter.emit_tool_call_args(tool_call_id, tool_input)

                elif event_name == "on_tool_end":
                    run_id_key = event.get("run_id", "")
                    tool_call_id = active_tool_calls.pop(run_id_key, None)
                    if tool_call_id:
                        yield emitter.emit_tool_call_end(tool_call_id)

                # Handle text streaming
                elif (
                    event_name == "on_chat_model_stream"
                    and event["data"]["chunk"].content
                ):
                    content = event["data"]["chunk"].content

                    text = ""
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block["text"]
                                break
                    elif isinstance(content, str):
                        text = content

                    if not text:
                        continue

                    if not message_started:
                        yield emitter.emit_text_start(message_id, "assistant")
                        message_started = True

                    yield emitter.emit_text_content(message_id, text)
                    full_response += text

            if message_started:
                yield emitter.emit_text_end(message_id)
                thread_store.add_message(
                    thread_id, {"role": "assistant", "content": full_response}
                )

        except Exception as e:
            logging.exception("Chat agent error")
            yield emitter.emit_run_error(str(e))
            return

        yield emitter.emit_run_finished(thread_id, run_id)

    raw_stream = event_stream()
    # Apply middleware chain: logging → capability filter → history
    stream = LoggingMiddleware().apply(
        CapabilityFilterMiddleware(
            allowed_types={
                "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
                "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END",
                "STATE_SNAPSHOT", "STATE_DELTA",
            }
        ).apply(
            HistoryMiddleware(store=thread_store, thread_id=thread_id).apply(raw_stream)
        )
    )

    return StreamingResponse(stream, media_type=emitter.content_type)
```

- [ ] **Step 4: Run tests and lint**

Run: `uv run pytest tests/ -v && uv run ruff check src/`
Expected: All PASS, no lint errors

- [ ] **Step 5: Commit**

```bash
git add src/agui_backend_demo/agent/chat/
git commit -m "feat(chat): add backend tools for multi-agent orchestration with tool call events"
```

---

## Phase 7: Frontend Shared Infrastructure

### Task 13: Create shared types and hooks

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/hooks/useThreadHistory.ts`

- [ ] **Step 1: Create shared types**

```typescript
// frontend/lib/types.ts
export interface Condition {
  field: string;
  operator: string;
  value: string | number | string[];
}

export interface ConditionGroup {
  logical_operator: "AND" | "OR";
  conditions: Condition[];
}

export interface Segment {
  name: string;
  description: string;
  condition_groups: ConditionGroup[];
  estimated_scope?: string;
}

export interface TemplateSection {
  id: string;
  type: string;
  content: string;
  styles?: Record<string, string>;
}

export interface EmailTemplate {
  html: string;
  css: string;
  subject: string;
  preview_text: string;
  sections: TemplateSection[];
  version: number;
}

export interface Campaign {
  name: string;
  segment_id: string | null;
  template_id: string | null;
  subject: string;
  send_time: string | null;
  status: string;
}

export interface CustomProperty {
  name: string;
  description: string;
  javascript_code: string;
  property_type: string;
  example_value: string | null;
}

export interface ThreadSummary {
  id: string;
  agent_type: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ThreadMessage {
  role: string;
  content: string;
}

export interface ThreadData {
  messages: ThreadMessage[];
  events: Record<string, unknown>[];
  state: Record<string, unknown>;
  agent_type: string;
  created_at: string;
  updated_at: string;
}
```

- [ ] **Step 2: Create useThreadHistory hook**

```typescript
// frontend/hooks/useThreadHistory.ts
"use client";

import { useState, useEffect, useCallback } from "react";
import type { ThreadSummary, ThreadData, ThreadMessage } from "@/lib/types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function useThreadHistory() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchThreads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/threads`);
      if (!res.ok) throw new Error(`Failed to fetch threads: ${res.status}`);
      const data = await res.json();
      setThreads(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchThreads();
  }, [fetchThreads]);

  return { threads, loading, error, refetch: fetchThreads };
}

export function useThreadMessages(threadId: string | null) {
  const [messages, setMessages] = useState<ThreadMessage[]>([]);
  const [threadData, setThreadData] = useState<ThreadData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = useCallback(async () => {
    if (!threadId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/threads/${threadId}`);
      if (!res.ok) throw new Error(`Thread not found: ${res.status}`);
      const data: ThreadData = await res.json();
      setThreadData(data);
      setMessages(data.messages);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [threadId]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  return { messages, threadData, loading, error, refetch: fetchMessages };
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/types.ts frontend/hooks/useThreadHistory.ts
git commit -m "feat(frontend): add shared TypeScript types and thread history hook"
```

---

### Task 14: Create frontend components

**Files:**
- Create: `frontend/components/TemplateEditor.tsx`
- Create: `frontend/components/TemplatePreview.tsx`
- Create: `frontend/components/CampaignBuilder.tsx`
- Create: `frontend/components/CustomPropertyCard.tsx`
- Create: `frontend/components/ActivityIndicator.tsx`
- Create: `frontend/components/ReasoningPanel.tsx`
- Create: `frontend/components/ThreadHistory.tsx`
- Modify: `frontend/components/Nav.tsx`

- [ ] **Step 1: Create TemplateEditor**

```tsx
// frontend/components/TemplateEditor.tsx
"use client";

import { useState } from "react";
import type { EmailTemplate, TemplateSection } from "@/lib/types";
import { TemplatePreview } from "./TemplatePreview";

interface TemplateEditorProps {
  template: EmailTemplate;
  onSectionChange?: (sectionId: string, content: string) => void;
}

export function TemplateEditor({ template, onSectionChange }: TemplateEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  return (
    <div className="flex gap-4 h-full">
      {/* Left: Editable sections */}
      <div className="flex-1 overflow-y-auto space-y-3 p-4">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Subject: {template.subject || "Untitled"}
          </h3>
          {template.preview_text && (
            <p className="text-xs text-gray-500 mt-1">{template.preview_text}</p>
          )}
          <span className="text-xs text-gray-400">v{template.version}</span>
        </div>

        {template.sections.map((section) => (
          <div
            key={section.id}
            className="border border-gray-200 dark:border-gray-700 rounded-lg p-3"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase">
                {section.type}
              </span>
              <button
                onClick={() => setEditingId(editingId === section.id ? null : section.id)}
                className="text-xs text-blue-500 hover:text-blue-700"
              >
                {editingId === section.id ? "Done" : "Edit"}
              </button>
            </div>

            {editingId === section.id ? (
              <textarea
                className="w-full h-32 text-xs font-mono bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded p-2"
                defaultValue={section.content}
                onBlur={(e) => onSectionChange?.(section.id, e.target.value)}
              />
            ) : (
              <div
                className="text-xs text-gray-600 dark:text-gray-400 font-mono truncate"
                title={section.content}
              >
                {section.content.substring(0, 200)}
                {section.content.length > 200 ? "..." : ""}
              </div>
            )}
          </div>
        ))}

        {template.sections.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">
            No sections yet. Describe your template in the chat to generate one.
          </p>
        )}
      </div>

      {/* Right: Live preview */}
      <div className="flex-1 border-l border-gray-200 dark:border-gray-700">
        <TemplatePreview html={template.html} css={template.css} />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create TemplatePreview**

```tsx
// frontend/components/TemplatePreview.tsx
interface TemplatePreviewProps {
  html: string;
  css: string;
}

export function TemplatePreview({ html, css }: TemplatePreviewProps) {
  const fullHtml = `
    <!DOCTYPE html>
    <html>
      <head><style>${css}</style></head>
      <body style="margin:0;padding:20px;background:#f5f5f5;">
        ${html || '<p style="text-align:center;color:#999;padding:40px;">Preview will appear here</p>'}
      </body>
    </html>
  `;

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-500">Preview</span>
      </div>
      <iframe
        srcDoc={fullHtml}
        className="flex-1 w-full bg-white"
        sandbox="allow-same-origin"
        title="Template Preview"
      />
    </div>
  );
}
```

- [ ] **Step 3: Create CampaignBuilder**

```tsx
// frontend/components/CampaignBuilder.tsx
import type { Campaign } from "@/lib/types";

export function CampaignBuilder({ campaign }: { campaign: Campaign }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden text-sm my-2 w-full">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {campaign.name}
          </span>
          <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${
            campaign.status === "draft"
              ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
              : campaign.status === "scheduled"
              ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
              : "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
          }`}>
            {campaign.status}
          </span>
        </div>
      </div>

      <div className="px-4 py-3 space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Subject:</span>
          <span className="text-gray-700 dark:text-gray-300">{campaign.subject || "—"}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Segment:</span>
          <span className="text-gray-700 dark:text-gray-300">{campaign.segment_id || "Not set"}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Template:</span>
          <span className="text-gray-700 dark:text-gray-300">{campaign.template_id || "Not set"}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Send Time:</span>
          <span className="text-gray-700 dark:text-gray-300">{campaign.send_time || "Not scheduled"}</span>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create CustomPropertyCard**

```tsx
// frontend/components/CustomPropertyCard.tsx
import type { CustomProperty } from "@/lib/types";

export function CustomPropertyCard({ property }: { property: CustomProperty }) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden text-sm my-2 w-full">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold font-mono text-gray-900 dark:text-gray-100">
            {property.name}
          </span>
          <span className="shrink-0 text-xs bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300 px-2 py-0.5 rounded-full">
            {property.property_type}
          </span>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mt-1 text-xs">
          {property.description}
        </p>
      </div>

      <div className="px-4 py-3">
        <div className="text-xs text-gray-500 mb-1 font-medium">JavaScript Code:</div>
        <pre className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 text-xs font-mono text-gray-700 dark:text-gray-300 overflow-x-auto">
          <code>{property.javascript_code}</code>
        </pre>
      </div>

      {property.example_value && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
          Example: <code className="font-mono">{property.example_value}</code>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Create ActivityIndicator**

```tsx
// frontend/components/ActivityIndicator.tsx
interface ActivityContent {
  title: string;
  progress: number;
  details: string;
}

interface ActivityIndicatorProps {
  activityType: string;
  content: ActivityContent;
}

export function ActivityIndicator({ activityType, content }: ActivityIndicatorProps) {
  const percentage = Math.round(content.progress * 100);

  return (
    <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-3 my-2 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
          {content.title}
        </span>
        <span className="text-xs text-blue-500 ml-auto">{percentage}%</span>
      </div>
      <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-1.5">
        <div
          className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">{content.details}</p>
    </div>
  );
}
```

- [ ] **Step 6: Create ReasoningPanel**

```tsx
// frontend/components/ReasoningPanel.tsx
"use client";

import { useState } from "react";

interface ReasoningPanelProps {
  reasoning: string;
  defaultOpen?: boolean;
}

export function ReasoningPanel({ reasoning, defaultOpen = false }: ReasoningPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!reasoning) return null;

  return (
    <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 my-2 text-sm overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 flex items-center gap-2 text-xs font-medium text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
      >
        <span className={`transition-transform ${isOpen ? "rotate-90" : ""}`}>
          &#9654;
        </span>
        Chain of Thought
      </button>
      {isOpen && (
        <div className="px-3 pb-3 text-xs text-amber-800 dark:text-amber-200 whitespace-pre-wrap font-mono">
          {reasoning}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 7: Create ThreadHistory**

```tsx
// frontend/components/ThreadHistory.tsx
"use client";

import Link from "next/link";
import { useThreadHistory } from "@/hooks/useThreadHistory";

const agentLabels: Record<string, string> = {
  chat: "Chat",
  segment: "Segment",
  template: "Template",
  campaign: "Campaign",
  custom_property: "Custom Property",
};

export function ThreadHistory() {
  const { threads, loading, error, refetch } = useThreadHistory();

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Thread History
        </span>
        <button
          onClick={refetch}
          className="text-xs text-blue-500 hover:text-blue-700"
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="px-4 py-2 text-xs text-red-500">Error: {error}</div>
      )}

      <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-80 overflow-y-auto">
        {threads.length === 0 ? (
          <p className="px-4 py-3 text-xs text-gray-400">No threads yet</p>
        ) : (
          threads.map((thread) => (
            <Link
              key={thread.id}
              href={`/thread/${thread.id}`}
              className="block px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {agentLabels[thread.agent_type] || thread.agent_type}
                </span>
                <span className="text-xs text-gray-400">
                  {thread.message_count} msg{thread.message_count !== 1 ? "s" : ""}
                </span>
              </div>
              <p className="text-xs text-gray-400 truncate">{thread.id}</p>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 8: Update Nav component**

Replace `frontend/components/Nav.tsx` with:

```tsx
// frontend/components/Nav.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/chat", label: "Chat" },
  { href: "/segment", label: "Segment" },
  { href: "/template", label: "Template" },
  { href: "/campaign", label: "Campaign" },
  { href: "/custom-property", label: "Properties" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between">
      <Link href="/" className="text-lg font-semibold">
        AG-UI Demo
      </Link>
      <nav className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        {links.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              pathname === href
                ? "bg-white dark:bg-gray-700 shadow-sm"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
```

- [ ] **Step 9: Commit**

```bash
git add frontend/components/ frontend/lib/ frontend/hooks/
git commit -m "feat(frontend): add all new components, shared types, and update navigation"
```

---

## Phase 8: Frontend New Pages

### Task 15: Create frontend API routes and agent pages

**Files:**
- Create: `frontend/app/api/copilotkit/template/route.ts`
- Create: `frontend/app/api/copilotkit/campaign/route.ts`
- Create: `frontend/app/api/copilotkit/custom-property/route.ts`
- Create: `frontend/app/template/page.tsx`
- Create: `frontend/app/campaign/page.tsx`
- Create: `frontend/app/custom-property/page.tsx`
- Create: `frontend/app/thread/[threadId]/page.tsx`
- Modify: `frontend/app/segment/page.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Create template API route**

```typescript
// frontend/app/api/copilotkit/template/route.ts
import {
  CopilotRuntime,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: `${BACKEND_URL}/api/v1/template`,
      description: "Email template creator with human-in-the-loop editing",
    }),
  },
});

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new EmptyAdapter(),
    endpoint: "/api/copilotkit/template",
  });
  return handleRequest(req);
};
```

- [ ] **Step 2: Create campaign API route**

```typescript
// frontend/app/api/copilotkit/campaign/route.ts
import {
  CopilotRuntime,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: `${BACKEND_URL}/api/v1/campaign`,
      description: "Email campaign builder",
    }),
  },
});

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new EmptyAdapter(),
    endpoint: "/api/copilotkit/campaign",
  });
  return handleRequest(req);
};
```

- [ ] **Step 3: Create custom-property API route**

```typescript
// frontend/app/api/copilotkit/custom-property/route.ts
import {
  CopilotRuntime,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: `${BACKEND_URL}/api/v1/custom-property`,
      description: "Custom user property generator",
    }),
  },
});

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new EmptyAdapter(),
    endpoint: "/api/copilotkit/custom-property",
  });
  return handleRequest(req);
};
```

- [ ] **Step 4: Create template page**

```tsx
// frontend/app/template/page.tsx
"use client";

import { CopilotKit, useCoAgentStateRender, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { TemplateEditor } from "@/components/TemplateEditor";
import type { EmailTemplate } from "@/lib/types";

function TemplatePageContent() {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.subject ? (
        <div className="my-2 p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs text-green-700 dark:text-green-300">
          Template updated: {state.subject}
        </div>
      ) : null,
  });

  const { state: template } = useCoAgent<EmailTemplate>({ name: "default" });

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 overflow-hidden">
        {template?.subject ? (
          <TemplateEditor template={template} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-gray-400">
              Describe your email template in the sidebar to get started.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function TemplatePage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/template">
      <CopilotSidebar
        defaultOpen={true}
        instructions="You are an email template design assistant. Help the user create and modify professional HTML email templates. Generate complete templates with sections for header, body, CTA, and footer."
        labels={{
          title: "Template Creator",
          initial:
            'Describe the email template you want to create.\n\nTry: **"A welcome email for new SaaS users with a hero image, feature highlights, and a CTA button"**',
        }}
      >
        <TemplatePageContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

- [ ] **Step 5: Create campaign page**

```tsx
// frontend/app/campaign/page.tsx
"use client";

import { CopilotKit, useCoAgentStateRender, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { CampaignBuilder } from "@/components/CampaignBuilder";
import type { Campaign } from "@/lib/types";

function CampaignPageContent() {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.name ? <CampaignBuilder campaign={state} /> : null,
  });

  const { state: campaign } = useCoAgent<Campaign>({ name: "default" });

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {campaign?.name ? (
          <div className="w-full max-w-lg">
            <CampaignBuilder campaign={campaign} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe your email campaign in the sidebar to build one.
          </p>
        )}
      </main>
    </div>
  );
}

export default function CampaignPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/campaign">
      <CopilotSidebar
        defaultOpen={true}
        instructions="You are an email campaign builder. Help the user create campaign definitions with name, subject, and scheduling details."
        labels={{
          title: "Campaign Builder",
          initial:
            'Describe the campaign you want to create.\n\nTry: **"A spring sale campaign targeting active US users"**',
        }}
      >
        <CampaignPageContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

- [ ] **Step 6: Create custom-property page**

```tsx
// frontend/app/custom-property/page.tsx
"use client";

import { CopilotKit, useCoAgentStateRender, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { CustomPropertyCard } from "@/components/CustomPropertyCard";
import type { CustomProperty } from "@/lib/types";

function CustomPropertyPageContent() {
  useCoAgentStateRender({
    name: "default",
    render: ({ state }) =>
      state?.name ? <CustomPropertyCard property={state} /> : null,
  });

  const { state: property } = useCoAgent<CustomProperty>({ name: "default" });

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 flex items-center justify-center p-8">
        {property?.name ? (
          <div className="w-full max-w-lg">
            <CustomPropertyCard property={property} />
          </div>
        ) : (
          <p className="text-sm text-gray-400">
            Describe the custom property you want in the sidebar.
          </p>
        )}
      </main>
    </div>
  );
}

export default function CustomPropertyPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit/custom-property">
      <CopilotSidebar
        defaultOpen={true}
        instructions="You are a custom property generator. Help the user create computed user properties with JavaScript code for segmentation."
        labels={{
          title: "Custom Properties",
          initial:
            'Describe the custom property you want to generate.\n\nTry: **"A boolean property that identifies power users who logged in 30+ times"**',
        }}
      >
        <CustomPropertyPageContent />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

- [ ] **Step 7: Create thread viewer page**

```tsx
// frontend/app/thread/[threadId]/page.tsx
"use client";

import { useParams } from "next/navigation";
import { Nav } from "@/components/Nav";
import { useThreadMessages } from "@/hooks/useThreadHistory";

export default function ThreadPage() {
  const params = useParams();
  const threadId = params.threadId as string;
  const { messages, threadData, loading, error } = useThreadMessages(threadId);

  return (
    <div className="h-screen flex flex-col">
      <Nav />
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Thread: {threadId}
            </h1>
            {threadData && (
              <p className="text-xs text-gray-500 mt-1">
                Agent: {threadData.agent_type} | Created: {new Date(threadData.created_at).toLocaleString()}
              </p>
            )}
          </div>

          {loading && <p className="text-sm text-gray-400">Loading...</p>}
          {error && <p className="text-sm text-red-500">Error: {error}</p>}

          <div className="space-y-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg text-sm ${
                  msg.role === "user"
                    ? "bg-blue-50 dark:bg-blue-900/20 ml-8"
                    : "bg-gray-50 dark:bg-gray-800 mr-8"
                }`}
              >
                <span className="text-xs font-medium text-gray-500 block mb-1">
                  {msg.role}
                </span>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {msg.content}
                </p>
              </div>
            ))}
            {messages.length === 0 && !loading && (
              <p className="text-sm text-gray-400 text-center py-8">
                No messages in this thread.
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 8: Update segment page to use shared types**

Replace the inline `Segment` interface in `frontend/app/segment/page.tsx` with an import:

Change the top of the file to:
```tsx
"use client";

import { CopilotKit, useCoAgentStateRender, useCoAgent } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { Nav } from "@/components/Nav";
import { SegmentCard } from "@/components/SegmentCard";
import type { Segment } from "@/lib/types";
```

Remove the inline `Segment` interface definition (lines 8-16 of the original file).

- [ ] **Step 9: Update home page**

Replace `frontend/app/page.tsx` with:

```tsx
// frontend/app/page.tsx
import Link from "next/link";
import { Nav } from "@/components/Nav";

const agents = [
  {
    href: "/chat",
    title: "All-Purpose Chat",
    description: "Multi-agent orchestrator with backend tools. Demonstrates middleware, capabilities, and tool call events.",
    concepts: ["Middleware", "Capabilities", "BE Tools", "Multi-Agent"],
  },
  {
    href: "/segment",
    title: "Segment Builder",
    description: "Generate audience segments with structured output. Demonstrates state snapshots and lifecycle events.",
    concepts: ["Events", "State Snapshots", "Messages", "Serialization"],
  },
  {
    href: "/template",
    title: "Template Creator",
    description: "Collaborative email template editor. Demonstrates state deltas, FE tools, activity, and reasoning events.",
    concepts: ["State Deltas", "FE Tools", "Activity", "Reasoning"],
  },
  {
    href: "/campaign",
    title: "Campaign Builder",
    description: "Compose segments and templates into campaigns. Demonstrates multi-agent state composition.",
    concepts: ["Multi-Agent State"],
  },
  {
    href: "/custom-property",
    title: "Custom Properties",
    description: "Generate computed properties with JavaScript code. Demonstrates custom events and generative UI.",
    concepts: ["Custom Events", "Generative UI"],
  },
];

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Nav />
      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            AG-UI Core Concepts Demo
          </h1>
          <p className="text-sm text-gray-500 mb-8">
            Email marketing AI assistant demonstrating all 11 AG-UI protocol concepts.
          </p>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map(({ href, title, description, concepts }) => (
              <Link
                key={href}
                href={href}
                className="block p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 hover:shadow-sm transition-all bg-white dark:bg-gray-900"
              >
                <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                  {title}
                </h2>
                <p className="text-xs text-gray-500 mb-3">{description}</p>
                <div className="flex flex-wrap gap-1">
                  {concepts.map((c) => (
                    <span
                      key={c}
                      className="text-xs bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 px-2 py-0.5 rounded-full"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 10: Commit**

```bash
git add frontend/app/ frontend/components/Nav.tsx
git commit -m "feat(frontend): add template, campaign, custom-property pages, thread viewer, and update home page"
```

---

## Phase 9: Documentation and Final Polish

### Task 16: Create agent README documentation

**Files:**
- Create: `src/agui_backend_demo/agent/segment/README.md`
- Create: `src/agui_backend_demo/agent/template/README.md`
- Create: `src/agui_backend_demo/agent/chat/README.md`
- Create: `src/agui_backend_demo/agent/campaign/README.md`
- Create: `src/agui_backend_demo/agent/custom_property/README.md`

- [ ] **Step 1: Create segment README**

```markdown
<!-- src/agui_backend_demo/agent/segment/README.md -->
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
```

- [ ] **Step 2: Create template README**

```markdown
<!-- src/agui_backend_demo/agent/template/README.md -->
# Template Creator Agent

## AG-UI Concepts Demonstrated

### State Deltas (JSON Patch)
- `STATE_SNAPSHOT` — emits full `EmailTemplate` on first generation
- `STATE_DELTA` — emits JSON Patch (RFC 6902) operations on template modifications
- Enables efficient incremental updates without resending entire state
- Operations: `add`, `replace`, `remove` on template fields

### Frontend-Defined Tools
- `update_section` — modifies an existing template section
- `add_section` — adds a new section to the template
- `remove_section` — removes a section from the template
- These are defined in `tools.py` as JSON schemas, NOT LangGraph tools
- Backend emits `TOOL_CALL_START` / `TOOL_CALL_ARGS` / `TOOL_CALL_END` events
- Frontend executes via `useCopilotAction` hook

### Activity Events
- `ACTIVITY_SNAPSHOT` — progress indicators showing what the agent is doing
- Stages: Analyzing (20%) → Generating (50%) → Styling (80%) → Finalizing (100%)
- Displayed as progress bar in frontend

### Reasoning Events
- `REASONING_START` → `REASONING_MESSAGE_START` → `REASONING_MESSAGE_CONTENT` (×N) → `REASONING_MESSAGE_END` → `REASONING_END`
- Shows chain-of-thought: template analysis, layout decisions, design rationale
- Displayed in collapsible ReasoningPanel component

### Human-in-the-Loop
- Bidirectional state: frontend can edit template sections, changes sent back to backend
- Backend reads frontend state to apply AI modifications on top of human edits

## Activity Event vs Reasoning Event
| | Activity Event | Reasoning Event |
|---|---|---|
| **Purpose** | WHAT the agent is doing | WHY/HOW the agent is thinking |
| **Audience** | End user progress updates | Developer/power user insight |
| **Format** | Brief status + progress bar | Detailed chain-of-thought text |
| **UI** | Inline progress indicator | Collapsible panel |
| **Example** | "Generating header section..." | "Single-column layouts render better across email clients..." |

## Files
- `graph.py` — Conditional routing: generate (new) vs modify (existing)
- `state.py` — `TemplateAgentState` with bidirectional version tracking
- `tools.py` — Frontend tool schemas (JSON, not LangGraph)
- `routes.py` — Full event lifecycle with reasoning, activity, state, and tool events
```

- [ ] **Step 3: Create chat README**

```markdown
<!-- src/agui_backend_demo/agent/chat/README.md -->
# All-Purpose Chat Agent

## AG-UI Concepts Demonstrated

### Middleware
Three middleware layers applied in the event pipeline:
1. `LoggingMiddleware` — logs every event type for debugging
2. `CapabilityFilterMiddleware` — filters events to only allowed types
3. `HistoryMiddleware` — stores all events in ThreadStore

Middleware composes via async generators: `Logging(CapabilityFilter(History(raw_stream)))`

### Capabilities
Agent declares its capabilities via `GET /api/v1/agents/capabilities`:
```json
{"streaming": true, "state": false, "tools": true, "reasoning": false, "multi_agent": true}
```
Frontend can query this to adapt UI features.

### Backend-Defined Tools (vs Frontend-Defined)
Three LangGraph `@tool` functions executed server-side:
- `generate_segment(description)` — calls the Segment Generator agent
- `create_template(brief)` — calls the Template Creator agent
- `generate_custom_property(description)` — calls the Custom Property Generator

These differ from template's frontend tools:
| | Backend Tools (Chat) | Frontend Tools (Template) |
|---|---|---|
| **Defined in** | Python `@tool` decorator | JSON schemas in `tools.py` |
| **Executed by** | Backend (LangGraph) | Frontend (`useCopilotAction`) |
| **Events** | `TOOL_CALL_START/ARGS/END` for transparency | `TOOL_CALL_START/ARGS/END` for execution |
| **Result** | Tool returns to agent directly | Frontend returns `TOOL_CALL_RESULT` |

### Multi-Agent Orchestration
Chat agent calls other agents as tools, creating a hub-and-spoke pattern.

### Messages
Demonstrates all message types:
- User messages (input)
- Assistant messages (streaming text)
- Tool messages (tool call results from backend tools)

## Files
- `graph.py` — `create_react_agent` with tools list
- `tools.py` — Backend `@tool` functions that invoke other agent graphs
- `routes.py` — Streaming with tool call event detection and middleware chain
```

- [ ] **Step 4: Create campaign README**

```markdown
<!-- src/agui_backend_demo/agent/campaign/README.md -->
# Campaign Builder Agent (Stub)

## AG-UI Concepts Demonstrated

### Multi-Agent State Composition
Campaign state combines data from multiple agents:
- `segment` — from Segment Generator
- `template` — from Template Creator
- `campaign` — campaign-specific metadata

In a full implementation, this agent would:
1. Call the Segment Generator to create/select a segment
2. Call the Template Creator to create/select a template
3. Compose them into a campaign with scheduling and delivery settings

### State Snapshots
- `STATE_SNAPSHOT` — emits the complete Campaign as JSON
- Campaign schema: name, segment_id, template_id, subject, send_time, status

## Files
- `graph.py` — Single-node graph with structured output
- `state.py` — `CampaignState` with segment and template slots
- `routes.py` — Standard SSE lifecycle with state snapshot
```

- [ ] **Step 5: Create custom property README**

```markdown
<!-- src/agui_backend_demo/agent/custom_property/README.md -->
# Custom Property Generator Agent (Stub)

## AG-UI Concepts Demonstrated

### Custom Events
- `CUSTOM` event with name `"property_generated"` and metadata value
- Custom events enable application-specific event types beyond the standard AG-UI protocol
- Frontend can listen for these to trigger custom UI behaviors

### Generative UI Concepts
The agent generates both:
1. A structured property definition (name, type, description)
2. Executable JavaScript code

This demonstrates the generative UI pattern where agents produce dynamic UI content
(in this case, a code editor component) rather than just text responses.

## Custom Event Payload
```json
{
  "type": "CUSTOM",
  "name": "property_generated",
  "value": {
    "property_name": "days_since_signup",
    "property_type": "number",
    "has_code": true
  }
}
```

## Files
- `graph.py` — Single-node graph with structured output for CustomProperty
- `state.py` — `CustomPropertyState` TypedDict
- `routes.py` — SSE lifecycle with CUSTOM event emission
```

- [ ] **Step 6: Commit**

```bash
git add src/agui_backend_demo/agent/*/README.md
git commit -m "docs: add AG-UI concept documentation for each agent"
```

---

### Task 17: Final lint, format, and test pass

**Files:**
- Modify: various (lint fixes)

- [ ] **Step 1: Run full lint and format**

```bash
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: All PASS

- [ ] **Step 3: Verify frontend compiles**

```bash
cd frontend && npm run build
```

Expected: Build succeeds

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "chore: lint, format, and verify full build"
```

---

## Verification

To test the complete implementation end-to-end:

1. **Start backend**: `just backend` (runs on :8000)
2. **Start frontend**: `just frontend` (runs on :3000)
3. **Test each agent page**:
   - `/chat` — send a message, ask it to "create a segment for US users" (triggers backend tool)
   - `/segment` — describe an audience, verify SegmentCard renders
   - `/template` — describe a template, verify split-pane editor renders
   - `/campaign` — describe a campaign, verify CampaignBuilder renders
   - `/custom-property` — describe a property, verify code block renders
4. **Test thread history**:
   - After using agents, visit `/api/v1/threads` to see all threads
   - Click a thread to view at `/thread/{threadId}`
5. **Test capabilities**: `curl http://localhost:8000/api/v1/agents/capabilities`
6. **Run tests**: `just test`
