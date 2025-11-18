"""
API tests using TestClient
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health():  # ← REMOVED @pytest.mark.asyncio
    """Test health check endpoint"""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_system_status():  # ← REMOVED @pytest.mark.asyncio
    """Test system status endpoint"""
    response = client.get("/health/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "databases" in data


def test_list_papers():  # ← REMOVED @pytest.mark.asyncio
    """Test list papers endpoint"""
    response = client.get("/api/papers/")
    assert response.status_code == 200
    data = response.json()
    assert "papers" in data
    assert "total" in data
    assert "page" in data


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
