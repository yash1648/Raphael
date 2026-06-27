"""Tests for the Raphael super-assistant API routes."""

from unittest.mock import patch, MagicMock


def test_raphael_status(client):
    """Test the Raphael status endpoint."""
    resp = client.get("/raphael/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Raphael"
    assert data["version"] == "1.0.0"
    assert "llm_providers" in data
    assert "memory_entries" in data
    assert "agents" in data
    assert "capabilities" in data


def test_llm_providers_endpoint(client):
    """Test listing LLM providers."""
    resp = client.get("/raphael/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "providers" in data
    assert "nvidia" in data["providers"]
    assert "openrouter" in data["providers"]
    assert "ollama" in data["providers"]
    assert len(data["providers"]) == 3


def test_memory_count(client):
    """Test memory count endpoint."""
    resp = client.get("/raphael/memory/count")
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data


def test_health_endpoint(client):
    """Test the main health endpoint."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["name"] == "Raphael"
