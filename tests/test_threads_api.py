"""Tests for threads and capabilities API endpoints."""

import pytest
from fastapi.testclient import TestClient

from agui_backend_demo.core.history import thread_store
from agui_backend_demo.main import app


@pytest.fixture(autouse=True)
def clear_store():
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


def test_get_thread_messages_not_found():
    response = client.get("/api/v1/threads/nonexistent/messages")
    assert response.status_code == 404


def test_capabilities_endpoint():
    response = client.get("/api/v1/agents/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "segment" in data
    assert "chat" in data
    assert "template" in data
    assert data["segment"]["streaming"] is True
