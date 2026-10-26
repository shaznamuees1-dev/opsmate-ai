"""
FastAPI TestClient integration tests.
Tests endpoints for health, incidents, summary, and chat fallback without external API calls.
"""

import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.incident import ChatResponse

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /api/health returns 200 with service details."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "opsmate-ai-backend"
    assert "version" in data
    assert "timestamp" in data
    assert "ai_ready" in data


def test_root_endpoint():
    """Verify GET / returns welcome JSON."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "documentation" in data


def test_list_incidents_endpoint():
    """Verify GET /api/incidents returns list with SLA calculations."""
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert isinstance(incidents, list)
    assert len(incidents) > 0

    first = incidents[0]
    assert "id" in first
    assert "title" in first
    assert "priority" in first
    assert "status" in first
    assert "sla" in first
    assert "sla_status" in first["sla"]
    assert "remaining_minutes" in first["sla"]


def test_list_incidents_with_query_params():
    """Verify GET /api/incidents filters work correctly."""
    response = client.get("/api/incidents?priority=P1&status=Open")
    assert response.status_code == 200
    incidents = response.json()
    for inc in incidents:
        assert inc["priority"] == "P1"
        assert inc["status"] == "Open"


def test_incident_summary_endpoint():
    """Verify GET /api/incidents/summary returns correct KPI structure."""
    response = client.get("/api/incidents/summary")
    assert response.status_code == 200
    summary = response.json()
    assert "total_incidents" in summary
    assert "active_incidents" in summary
    assert "p1_incidents" in summary
    assert "at_risk_incidents" in summary
    assert "breached_incidents" in summary
    assert summary["total_incidents"] >= summary["active_incidents"]


def test_single_incident_endpoint():
    """Verify GET /api/incidents/{id} returns 200 for valid ID and 404 for invalid."""
    response = client.get("/api/incidents/INC-1001")
    assert response.status_code == 200
    assert response.json()["id"] == "INC-1001"

    missing_response = client.get("/api/incidents/INC-NONEXISTENT")
    assert missing_response.status_code == 404


def test_chat_endpoint_missing_api_key(monkeypatch):
    """
    CRITICAL: Verify chat endpoint behavior when Groq API key is missing.
    Must return a graceful fallback message without 500 error or external calls.
    """
    # Ensure GROQ_API_KEY is not set or empty
    monkeypatch.setenv("GROQ_API_KEY", "")

    response = client.post("/api/chat", json={"message": "Which P1 incidents are open?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fallback"
    assert "Groq API key is not configured" in data["response"]
    assert data["tools_used"] == []


def test_chat_endpoint_placeholder_api_key(monkeypatch):
    """Verify chat endpoint when GROQ_API_KEY is set to placeholder."""
    monkeypatch.setenv("GROQ_API_KEY", "your_groq_api_key_here")

    response = client.post("/api/chat", json={"message": "Summarize urgent incidents."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fallback"
    assert "GROQ_API_KEY" in data["response"]


def test_chat_endpoint_with_mocked_assistant():
    """Verify chat endpoint successfully returns assistant response and tools when mocked."""
    mock_return = ChatResponse(
        response="There is 1 active P1 incident: Production Database Connection Pool Exhaustion.",
        tools_used=["list_incidents", "calculate_sla_risk"],
        status="success",
    )

    with patch("app.api.routes.run_ops_assistant", return_value=mock_return):
        response = client.post("/api/chat", json={"message": "Which P1 incidents are active?"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Production Database" in data["response"]
        assert "list_incidents" in data["tools_used"]
        assert "calculate_sla_risk" in data["tools_used"]
