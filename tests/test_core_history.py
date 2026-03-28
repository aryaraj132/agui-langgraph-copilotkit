"""Tests for agui_backend_demo.core.history module."""

from datetime import datetime

import pytest

from agui_backend_demo.core.history import ThreadStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def store() -> ThreadStore:
    """Return a fresh ThreadStore for each test."""
    return ThreadStore()


# ---------------------------------------------------------------------------
# create_thread tests
# ---------------------------------------------------------------------------


class TestCreateThread:
    """Tests for ThreadStore.create_thread."""

    def test_creates_thread_with_correct_fields(self, store: ThreadStore):
        thread = store.create_thread("t1", "chat")
        assert thread["agent_type"] == "chat"
        assert thread["messages"] == []
        assert thread["events"] == []
        assert thread["state"] == {}
        assert "created_at" in thread
        assert "updated_at" in thread

    def test_timestamps_are_utc_iso_format(self, store: ThreadStore):
        thread = store.create_thread("t1", "chat")
        # Should parse without error
        created = datetime.fromisoformat(thread["created_at"])
        updated = datetime.fromisoformat(thread["updated_at"])
        assert created.tzinfo is not None
        assert updated.tzinfo is not None

    def test_created_and_updated_at_match_on_creation(self, store: ThreadStore):
        thread = store.create_thread("t1", "chat")
        assert thread["created_at"] == thread["updated_at"]


# ---------------------------------------------------------------------------
# get_thread tests
# ---------------------------------------------------------------------------


class TestGetThread:
    """Tests for ThreadStore.get_thread."""

    def test_returns_existing_thread(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        thread = store.get_thread("t1")
        assert thread is not None
        assert thread["agent_type"] == "chat"

    def test_returns_none_for_missing_thread(self, store: ThreadStore):
        result = store.get_thread("nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# list_threads tests
# ---------------------------------------------------------------------------


class TestListThreads:
    """Tests for ThreadStore.list_threads."""

    def test_empty_store_returns_empty_list(self, store: ThreadStore):
        assert store.list_threads() == []

    def test_returns_summaries_with_correct_fields(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        store.create_thread("t2", "segment")
        summaries = store.list_threads()
        assert len(summaries) == 2

        ids = {s["id"] for s in summaries}
        assert ids == {"t1", "t2"}

        for summary in summaries:
            assert "id" in summary
            assert "agent_type" in summary
            assert "message_count" in summary
            assert "created_at" in summary
            assert "updated_at" in summary

    def test_message_count_reflects_added_messages(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        store.add_message("t1", {"role": "user", "content": "hello"})
        store.add_message("t1", {"role": "assistant", "content": "hi"})

        summaries = store.list_threads()
        assert summaries[0]["message_count"] == 2

    def test_summaries_do_not_include_full_data(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        summaries = store.list_threads()
        summary = summaries[0]
        assert "messages" not in summary
        assert "events" not in summary
        assert "state" not in summary


# ---------------------------------------------------------------------------
# add_message tests
# ---------------------------------------------------------------------------


class TestAddMessage:
    """Tests for ThreadStore.add_message."""

    def test_adds_message_to_thread(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        msg = {"role": "user", "content": "hello"}
        store.add_message("t1", msg)

        thread = store.get_thread("t1")
        assert len(thread["messages"]) == 1
        stored = thread["messages"][0]
        assert stored["role"] == "user"
        assert stored["content"] == "hello"
        assert "id" in stored  # auto-generated stable ID

    def test_updates_updated_at_timestamp(self, store: ThreadStore):
        thread = store.create_thread("t1", "chat")
        original_updated = thread["updated_at"]

        store.add_message("t1", {"role": "user", "content": "hello"})

        thread = store.get_thread("t1")
        assert thread["updated_at"] >= original_updated

    def test_raises_on_missing_thread(self, store: ThreadStore):
        with pytest.raises(KeyError):
            store.add_message("nonexistent", {"role": "user", "content": "hello"})


# ---------------------------------------------------------------------------
# add_event tests
# ---------------------------------------------------------------------------


class TestAddEvent:
    """Tests for ThreadStore.add_event."""

    def test_adds_event_to_thread(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        event = {"type": "RUN_STARTED", "threadId": "t1"}
        store.add_event("t1", event)

        thread = store.get_thread("t1")
        assert len(thread["events"]) == 1
        assert thread["events"][0] == event

    def test_updates_updated_at_timestamp(self, store: ThreadStore):
        thread = store.create_thread("t1", "chat")
        original_updated = thread["updated_at"]

        store.add_event("t1", {"type": "RUN_STARTED"})

        thread = store.get_thread("t1")
        assert thread["updated_at"] >= original_updated

    def test_raises_on_missing_thread(self, store: ThreadStore):
        with pytest.raises(KeyError):
            store.add_event("nonexistent", {"type": "RUN_STARTED"})


# ---------------------------------------------------------------------------
# update_state tests
# ---------------------------------------------------------------------------


class TestUpdateState:
    """Tests for ThreadStore.update_state."""

    def test_updates_state(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        store.update_state("t1", {"count": 5})

        thread = store.get_thread("t1")
        assert thread["state"] == {"count": 5}

    def test_merges_state(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        store.update_state("t1", {"a": 1})
        store.update_state("t1", {"b": 2})

        thread = store.get_thread("t1")
        assert thread["state"] == {"a": 1, "b": 2}

    def test_updates_updated_at_timestamp(self, store: ThreadStore):
        thread = store.create_thread("t1", "chat")
        original_updated = thread["updated_at"]

        store.update_state("t1", {"key": "value"})

        thread = store.get_thread("t1")
        assert thread["updated_at"] >= original_updated

    def test_raises_on_missing_thread(self, store: ThreadStore):
        with pytest.raises(KeyError):
            store.update_state("nonexistent", {"key": "value"})


# ---------------------------------------------------------------------------
# get_or_create_thread tests
# ---------------------------------------------------------------------------


class TestGetOrCreateThread:
    """Tests for ThreadStore.get_or_create_thread."""

    def test_creates_new_thread_when_missing(self, store: ThreadStore):
        thread = store.get_or_create_thread("t1", "chat")
        assert thread["agent_type"] == "chat"
        assert thread["messages"] == []

    def test_returns_existing_thread(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        store.add_message("t1", {"role": "user", "content": "hello"})

        thread = store.get_or_create_thread("t1", "chat")
        assert len(thread["messages"]) == 1

    def test_is_idempotent(self, store: ThreadStore):
        thread1 = store.get_or_create_thread("t1", "chat")
        thread2 = store.get_or_create_thread("t1", "chat")
        assert thread1["created_at"] == thread2["created_at"]

    def test_does_not_overwrite_existing_data(self, store: ThreadStore):
        store.create_thread("t1", "chat")
        store.add_message("t1", {"role": "user", "content": "hello"})
        store.update_state("t1", {"count": 5})

        thread = store.get_or_create_thread("t1", "chat")
        assert len(thread["messages"]) == 1
        assert thread["state"] == {"count": 5}


# ---------------------------------------------------------------------------
# Module-level singleton tests
# ---------------------------------------------------------------------------


class TestModuleSingleton:
    """Tests for the module-level thread_store singleton."""

    def test_singleton_is_thread_store_instance(self):
        from agui_backend_demo.core.history import thread_store

        assert isinstance(thread_store, ThreadStore)

    def test_singleton_is_same_object_on_reimport(self):
        from agui_backend_demo.core.history import thread_store as store1
        from agui_backend_demo.core.history import thread_store as store2

        assert store1 is store2
