import pytest


@pytest.mark.integration
def test_health_endpoints(client):
    response = client.get("/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    readiness = client.get("/health/readiness")
    assert readiness.status_code == 200
