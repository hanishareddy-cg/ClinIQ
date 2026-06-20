async def test_health_returns_ok(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_checks_services(async_client, mock_es):
    mock_es.ping.return_value = True
    response = await async_client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["postgres"] is True
    assert data["elasticsearch"] is True
    assert data["status"] == "ready"
