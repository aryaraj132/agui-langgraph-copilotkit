"""Tests for agui_backend_demo.core.middleware module."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import pytest

from agui_backend_demo.core.middleware import (
    CapabilityFilterMiddleware,
    HistoryMiddleware,
    LoggingMiddleware,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _mock_stream(*events: dict[str, Any]) -> AsyncIterator[str]:
    """Create mock async generator of SSE-formatted events."""
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"


async def _collect(stream: AsyncIterator[str]) -> list[str]:
    """Collect all items from an async generator."""
    items: list[str] = []
    async for item in stream:
        items.append(item)
    return items


def _parse_sse(sse_string: str) -> dict[str, Any]:
    """Parse an SSE-formatted string and return the JSON payload."""
    json_str = sse_string[len("data: ") :].rstrip("\n")
    return json.loads(json_str)


# ---------------------------------------------------------------------------
# LoggingMiddleware tests
# ---------------------------------------------------------------------------


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_passes_all_events_through_unchanged(self):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hi"},
            {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
        ]
        middleware = LoggingMiddleware()
        result = await _collect(middleware.apply(_mock_stream(*events)))

        assert len(result) == 3
        for original, output in zip(events, result):
            payload = _parse_sse(output)
            assert payload == original

    @pytest.mark.asyncio
    async def test_logs_event_types(self, caplog):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hi"},
        ]
        middleware = LoggingMiddleware()
        with caplog.at_level(logging.INFO):
            await _collect(middleware.apply(_mock_stream(*events)))

        assert "RUN_STARTED" in caplog.text
        assert "TEXT_MESSAGE_CONTENT" in caplog.text

    @pytest.mark.asyncio
    async def test_handles_empty_stream(self):
        middleware = LoggingMiddleware()
        result = await _collect(middleware.apply(_mock_stream()))
        assert result == []


# ---------------------------------------------------------------------------
# CapabilityFilterMiddleware tests
# ---------------------------------------------------------------------------


class TestCapabilityFilterMiddleware:
    """Tests for CapabilityFilterMiddleware."""

    @pytest.mark.asyncio
    async def test_drops_non_allowed_events(self):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hi"},
            {"type": "TOOL_CALL_START", "toolCallId": "tc1", "toolCallName": "s"},
            {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
        ]
        # Only allow TEXT_MESSAGE_CONTENT; lifecycle events should still pass
        middleware = CapabilityFilterMiddleware(allowed_types={"TEXT_MESSAGE_CONTENT"})
        result = await _collect(middleware.apply(_mock_stream(*events)))

        types = [_parse_sse(e)["type"] for e in result]
        assert "RUN_STARTED" in types  # lifecycle - always passes
        assert "TEXT_MESSAGE_CONTENT" in types  # explicitly allowed
        assert "TOOL_CALL_START" not in types  # not allowed, dropped
        assert "RUN_FINISHED" in types  # lifecycle - always passes

    @pytest.mark.asyncio
    async def test_keeps_lifecycle_events_always(self):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "RUN_ERROR", "message": "oops"},
            {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
        ]
        # Empty allowed set - only lifecycle types should pass
        middleware = CapabilityFilterMiddleware(allowed_types=set())
        result = await _collect(middleware.apply(_mock_stream(*events)))

        types = [_parse_sse(e)["type"] for e in result]
        assert types == ["RUN_STARTED", "RUN_ERROR", "RUN_FINISHED"]

    @pytest.mark.asyncio
    async def test_keeps_explicitly_allowed_event_types(self):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "TEXT_MESSAGE_START", "messageId": "m1", "role": "assistant"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hi"},
            {"type": "TEXT_MESSAGE_END", "messageId": "m1"},
            {"type": "TOOL_CALL_START", "toolCallId": "tc1", "toolCallName": "s"},
            {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
        ]
        middleware = CapabilityFilterMiddleware(
            allowed_types={
                "TEXT_MESSAGE_START",
                "TEXT_MESSAGE_CONTENT",
                "TEXT_MESSAGE_END",
            }
        )
        result = await _collect(middleware.apply(_mock_stream(*events)))

        types = [_parse_sse(e)["type"] for e in result]
        assert types == [
            "RUN_STARTED",
            "TEXT_MESSAGE_START",
            "TEXT_MESSAGE_CONTENT",
            "TEXT_MESSAGE_END",
            "RUN_FINISHED",
        ]

    @pytest.mark.asyncio
    async def test_handles_empty_stream(self):
        middleware = CapabilityFilterMiddleware(allowed_types={"TEXT_MESSAGE_CONTENT"})
        result = await _collect(middleware.apply(_mock_stream()))
        assert result == []


# ---------------------------------------------------------------------------
# HistoryMiddleware tests
# ---------------------------------------------------------------------------


class MockStore:
    """A minimal mock that records add_event calls."""

    def __init__(self) -> None:
        self.recorded: list[tuple[str, dict[str, Any]]] = []

    def add_event(self, thread_id: str, event: dict[str, Any]) -> None:
        self.recorded.append((thread_id, event))


class TestHistoryMiddleware:
    """Tests for HistoryMiddleware."""

    @pytest.mark.asyncio
    async def test_stores_events_in_mock_store(self):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hi"},
            {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
        ]
        mock_store = MockStore()
        middleware = HistoryMiddleware(store=mock_store, thread_id="t1")
        result = await _collect(middleware.apply(_mock_stream(*events)))

        # All events should still pass through
        assert len(result) == 3

        # All events should be recorded in the store
        assert len(mock_store.recorded) == 3
        for (tid, recorded_event), original in zip(mock_store.recorded, events):
            assert tid == "t1"
            assert recorded_event == original

    @pytest.mark.asyncio
    async def test_yields_events_unchanged(self):
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
        ]
        mock_store = MockStore()
        middleware = HistoryMiddleware(store=mock_store, thread_id="t1")
        result = await _collect(middleware.apply(_mock_stream(*events)))

        payload = _parse_sse(result[0])
        assert payload == events[0]

    @pytest.mark.asyncio
    async def test_handles_empty_stream(self):
        mock_store = MockStore()
        middleware = HistoryMiddleware(store=mock_store, thread_id="t1")
        result = await _collect(middleware.apply(_mock_stream()))
        assert result == []
        assert mock_store.recorded == []


# ---------------------------------------------------------------------------
# Middleware composition tests
# ---------------------------------------------------------------------------


class TestMiddlewareComposition:
    """Test that middlewares compose correctly."""

    @pytest.mark.asyncio
    async def test_composition_pipeline(self):
        """LoggingMiddleware -> CapabilityFilter -> HistoryMiddleware -> raw."""
        events = [
            {"type": "RUN_STARTED", "threadId": "t1", "runId": "r1"},
            {"type": "TEXT_MESSAGE_CONTENT", "messageId": "m1", "delta": "Hi"},
            {"type": "TOOL_CALL_START", "toolCallId": "tc1", "toolCallName": "s"},
            {"type": "RUN_FINISHED", "threadId": "t1", "runId": "r1"},
        ]

        mock_store = MockStore()
        raw = _mock_stream(*events)

        # Compose: history records everything, filter drops TOOL_CALL_START,
        # logging passes through
        pipeline = LoggingMiddleware().apply(
            CapabilityFilterMiddleware(allowed_types={"TEXT_MESSAGE_CONTENT"}).apply(
                HistoryMiddleware(store=mock_store, thread_id="t1").apply(raw)
            )
        )
        result = await _collect(pipeline)

        # History sees all 4 events (innermost)
        assert len(mock_store.recorded) == 4

        # Filter drops TOOL_CALL_START -> 3 events reach logging/output
        types = [_parse_sse(e)["type"] for e in result]
        assert types == ["RUN_STARTED", "TEXT_MESSAGE_CONTENT", "RUN_FINISHED"]
