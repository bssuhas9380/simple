"""Unit tests for the Task Queue Service."""
import json
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"


def test_create_task(client):
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "test_task", "priority": "high"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "test_task"
    assert data["priority"] == "high"
    assert data["status"] == "pending"


def test_create_task_missing_name(client):
    resp = client.post(
        "/api/v1/tasks",
        json={"priority": "high"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_list_tasks(client):
    client.post("/api/v1/tasks", json={"name": "t1"}, content_type="application/json")
    client.post("/api/v1/tasks", json={"name": "t2"}, content_type="application/json")
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 2
