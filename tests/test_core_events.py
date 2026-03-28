"""Tests for agui_backend_demo.core.events module."""

import json


from agui_backend_demo.core.events import EventEmitter, extract_user_query, get_field


# ---------------------------------------------------------------------------
# get_field tests
# ---------------------------------------------------------------------------


class TestGetField:
    """Tests for the get_field utility."""

    def test_snake_case_key(self):
        body = {"thread_id": "t1"}
        assert get_field(body, "thread_id", "threadId") == "t1"

    def test_camel_case_key(self):
        body = {"threadId": "t1"}
        assert get_field(body, "thread_id", "threadId") == "t1"

    def test_snake_takes_precedence(self):
        body = {"thread_id": "snake", "threadId": "camel"}
        assert get_field(body, "thread_id", "threadId") == "snake"

    def test_default_when_missing(self):
        body = {}
        assert get_field(body, "thread_id", "threadId") is None

    def test_custom_default(self):
        body = {}
        assert (
            get_field(body, "thread_id", "threadId", default="fallback") == "fallback"
        )

    def test_false_value_not_default(self):
        body = {"enabled": False}
        assert get_field(body, "enabled", "enabled", default=True) is False

    def test_empty_string_not_default(self):
        body = {"name": ""}
        assert get_field(body, "name", "name", default="unknown") == ""


# ---------------------------------------------------------------------------
# extract_user_query tests
# ---------------------------------------------------------------------------


class TestExtractUserQuery:
    """Tests for the extract_user_query utility."""

    def test_string_content(self):
        messages = [
            {"role": "user", "content": "Hello world"},
        ]
        assert extract_user_query(messages) == "Hello world"

    def test_list_content_text_parts(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "part one"},
                    {"type": "text", "text": "part two"},
                ],
            },
        ]
        result = extract_user_query(messages)
        assert "part one" in result
        assert "part two" in result

    def test_list_content_skips_non_text(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "url": "http://example.com/img.png"},
                    {"type": "text", "text": "describe this"},
                ],
            },
        ]
        assert extract_user_query(messages) == "describe this"

    def test_last_user_message(self):
        messages = [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "answer"},
            {"role": "user", "content": "second question"},
        ]
        assert extract_user_query(messages) == "second question"

    def test_empty_messages(self):
        assert extract_user_query([]) == ""

    def test_no_user_messages(self):
        messages = [
            {"role": "assistant", "content": "hello"},
        ]
        assert extract_user_query(messages) == ""


# ---------------------------------------------------------------------------
# EventEmitter tests
# ---------------------------------------------------------------------------


def _parse_sse(sse_string: str) -> dict:
    """Parse an SSE-formatted string and return the JSON payload."""
    assert sse_string.startswith("data: "), f"Expected SSE format, got: {sse_string!r}"
    assert sse_string.endswith("\n\n"), (
        f"Expected trailing newlines, got: {sse_string!r}"
    )
    json_str = sse_string[len("data: ") :].rstrip("\n")
    return json.loads(json_str)


class TestEventEmitterContentType:
    """Test the content_type property."""

    def test_content_type(self):
        emitter = EventEmitter()
        assert emitter.content_type == "text/event-stream"


class TestEmitRunEvents:
    """Test run lifecycle events."""

    def test_run_started(self):
        emitter = EventEmitter()
        result = emitter.emit_run_started("thread-1", "run-1")
        payload = _parse_sse(result)
        assert payload["type"] == "RUN_STARTED"
        assert payload["threadId"] == "thread-1"
        assert payload["runId"] == "run-1"

    def test_run_finished(self):
        emitter = EventEmitter()
        result = emitter.emit_run_finished("thread-1", "run-1")
        payload = _parse_sse(result)
        assert payload["type"] == "RUN_FINISHED"
        assert payload["threadId"] == "thread-1"
        assert payload["runId"] == "run-1"

    def test_run_error(self):
        emitter = EventEmitter()
        result = emitter.emit_run_error("Something went wrong")
        payload = _parse_sse(result)
        assert payload["type"] == "RUN_ERROR"
        assert payload["message"] == "Something went wrong"


class TestEmitStepEvents:
    """Test step lifecycle events."""

    def test_step_start(self):
        emitter = EventEmitter()
        result = emitter.emit_step_start("processing")
        payload = _parse_sse(result)
        assert payload["type"] == "STEP_STARTED"
        assert payload["stepName"] == "processing"

    def test_step_finish(self):
        emitter = EventEmitter()
        result = emitter.emit_step_finish("processing")
        payload = _parse_sse(result)
        assert payload["type"] == "STEP_FINISHED"
        assert payload["stepName"] == "processing"


class TestEmitTextMessageEvents:
    """Test text message streaming events."""

    def test_text_start(self):
        emitter = EventEmitter()
        result = emitter.emit_text_start("msg-1", "assistant")
        payload = _parse_sse(result)
        assert payload["type"] == "TEXT_MESSAGE_START"
        assert payload["messageId"] == "msg-1"
        assert payload["role"] == "assistant"

    def test_text_content(self):
        emitter = EventEmitter()
        result = emitter.emit_text_content("msg-1", "Hello ")
        payload = _parse_sse(result)
        assert payload["type"] == "TEXT_MESSAGE_CONTENT"
        assert payload["messageId"] == "msg-1"
        assert payload["delta"] == "Hello "

    def test_text_end(self):
        emitter = EventEmitter()
        result = emitter.emit_text_end("msg-1")
        payload = _parse_sse(result)
        assert payload["type"] == "TEXT_MESSAGE_END"
        assert payload["messageId"] == "msg-1"


class TestEmitStateEvents:
    """Test state snapshot and delta events."""

    def test_state_snapshot(self):
        emitter = EventEmitter()
        snapshot = {"count": 10, "items": ["a", "b"]}
        result = emitter.emit_state_snapshot(snapshot)
        payload = _parse_sse(result)
        assert payload["type"] == "STATE_SNAPSHOT"
        assert payload["snapshot"] == snapshot

    def test_state_delta(self):
        emitter = EventEmitter()
        delta = [{"op": "replace", "path": "/count", "value": 42}]
        result = emitter.emit_state_delta(delta)
        payload = _parse_sse(result)
        assert payload["type"] == "STATE_DELTA"
        assert payload["delta"] == delta


class TestEmitToolCallEvents:
    """Test tool call events."""

    def test_tool_call_start(self):
        emitter = EventEmitter()
        result = emitter.emit_tool_call_start("tc-1", "search")
        payload = _parse_sse(result)
        assert payload["type"] == "TOOL_CALL_START"
        assert payload["toolCallId"] == "tc-1"
        assert payload["toolCallName"] == "search"

    def test_tool_call_start_with_parent(self):
        emitter = EventEmitter()
        result = emitter.emit_tool_call_start(
            "tc-1", "search", parent_message_id="pm-1"
        )
        payload = _parse_sse(result)
        assert payload["type"] == "TOOL_CALL_START"
        assert payload["parentMessageId"] == "pm-1"

    def test_tool_call_args(self):
        emitter = EventEmitter()
        result = emitter.emit_tool_call_args("tc-1", '{"query":"test"}')
        payload = _parse_sse(result)
        assert payload["type"] == "TOOL_CALL_ARGS"
        assert payload["toolCallId"] == "tc-1"
        assert payload["delta"] == '{"query":"test"}'

    def test_tool_call_end(self):
        emitter = EventEmitter()
        result = emitter.emit_tool_call_end("tc-1")
        payload = _parse_sse(result)
        assert payload["type"] == "TOOL_CALL_END"
        assert payload["toolCallId"] == "tc-1"


class TestEmitActivityEvents:
    """Test activity snapshot events."""

    def test_activity_snapshot(self):
        emitter = EventEmitter()
        result = emitter.emit_activity_snapshot("msg-1", "thinking", "Working on it...")
        payload = _parse_sse(result)
        assert payload["type"] == "ACTIVITY_SNAPSHOT"
        assert payload["messageId"] == "msg-1"
        assert payload["activityType"] == "thinking"
        assert payload["content"] == "Working on it..."
        assert payload["replace"] is True

    def test_activity_snapshot_no_replace(self):
        emitter = EventEmitter()
        result = emitter.emit_activity_snapshot(
            "msg-1", "thinking", "Update", replace=False
        )
        payload = _parse_sse(result)
        assert payload["replace"] is False


class TestEmitReasoningEvents:
    """Test reasoning lifecycle events."""

    def test_reasoning_start(self):
        emitter = EventEmitter()
        result = emitter.emit_reasoning_start("msg-1")
        payload = _parse_sse(result)
        assert payload["type"] == "REASONING_START"
        assert payload["messageId"] == "msg-1"

    def test_reasoning_message_start(self):
        emitter = EventEmitter()
        result = emitter.emit_reasoning_message_start("msg-1")
        payload = _parse_sse(result)
        assert payload["type"] == "REASONING_MESSAGE_START"
        assert payload["messageId"] == "msg-1"
        assert payload["role"] == "reasoning"

    def test_reasoning_content(self):
        emitter = EventEmitter()
        result = emitter.emit_reasoning_content("msg-1", "Let me think...")
        payload = _parse_sse(result)
        assert payload["type"] == "REASONING_MESSAGE_CONTENT"
        assert payload["messageId"] == "msg-1"
        assert payload["delta"] == "Let me think..."

    def test_reasoning_message_end(self):
        emitter = EventEmitter()
        result = emitter.emit_reasoning_message_end("msg-1")
        payload = _parse_sse(result)
        assert payload["type"] == "REASONING_MESSAGE_END"
        assert payload["messageId"] == "msg-1"

    def test_reasoning_end(self):
        emitter = EventEmitter()
        result = emitter.emit_reasoning_end("msg-1")
        payload = _parse_sse(result)
        assert payload["type"] == "REASONING_END"
        assert payload["messageId"] == "msg-1"


class TestEmitCustomEvent:
    """Test custom events."""

    def test_custom_event(self):
        emitter = EventEmitter()
        result = emitter.emit_custom("my_event", {"key": "value"})
        payload = _parse_sse(result)
        assert payload["type"] == "CUSTOM"
        assert payload["name"] == "my_event"
        assert payload["value"] == {"key": "value"}

    def test_custom_event_string_value(self):
        emitter = EventEmitter()
        result = emitter.emit_custom("status", "ok")
        payload = _parse_sse(result)
        assert payload["value"] == "ok"


class TestEmitMessagesSnapshot:
    """Test messages snapshot events."""

    def test_messages_snapshot(self):
        emitter = EventEmitter()
        messages = [
            {"id": "m1", "role": "user", "content": "hello"},
            {"id": "m2", "role": "assistant", "content": "hi there"},
        ]
        result = emitter.emit_messages_snapshot(messages)
        payload = _parse_sse(result)
        assert payload["type"] == "MESSAGES_SNAPSHOT"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][1]["role"] == "assistant"


class TestEventEmitterSequence:
    """Test a realistic sequence of events from a single emitter."""

    def test_full_message_sequence(self):
        emitter = EventEmitter()
        events = []

        events.append(emitter.emit_run_started("t1", "r1"))
        events.append(emitter.emit_text_start("m1", "assistant"))
        events.append(emitter.emit_text_content("m1", "Hello"))
        events.append(emitter.emit_text_content("m1", " world"))
        events.append(emitter.emit_text_end("m1"))
        events.append(emitter.emit_run_finished("t1", "r1"))

        # All should be valid SSE
        for event_str in events:
            assert event_str.startswith("data: ")
            assert event_str.endswith("\n\n")

        # Verify sequence of types
        types = [_parse_sse(e)["type"] for e in events]
        assert types == [
            "RUN_STARTED",
            "TEXT_MESSAGE_START",
            "TEXT_MESSAGE_CONTENT",
            "TEXT_MESSAGE_CONTENT",
            "TEXT_MESSAGE_END",
            "RUN_FINISHED",
        ]
