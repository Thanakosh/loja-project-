def test_health_async_endpoint(client):
    response = client.get("/api/v2/health-async")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "async",
        "result": 1,
    }
