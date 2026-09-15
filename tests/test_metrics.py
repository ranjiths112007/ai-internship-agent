from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_metrics_endpoint_returns_persisted_shape():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"jobs", "applications"}
    assert set(data["jobs"]) == {"total", "high_fit", "international_remote"}
    assert set(data["applications"]) == {"total", "by_status"}
    assert isinstance(data["applications"]["by_status"], dict)
