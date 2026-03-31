def test_health_live_endpoint(client):
    response = client.get("/api/v2/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "checks": {
            "api": {
                "status": "ok",
            }
        },
    }


def test_health_ready_endpoint(client):
    response = client.get("/api/v2/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "checks": {
            "database": {
                "status": "ok",
                "mode": "async",
                "result": 1,
            }
        },
    }


def test_health_async_legacy_endpoint(client):
    response = client.get("/api/v2/health-async")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "async",
        "result": 1,
    }
