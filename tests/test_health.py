def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["health"] == "/api/health"


def test_top_level_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "services" in data
    assert "backend" in data["services"]
    assert "database" in data["services"]


def test_versioned_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]


def test_payment_order_stub(client):
    payload = {
        "amount": 50000,
        "currency": "INR",
        "receipt": "rcpt_test_001",
        "notes": {"invoice_id": "INV-2026-001"}
    }
    response = client.post("/api/v1/payments/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["amount"] == 50000


def test_ai_analyze_stub(client):
    payload = {
        "customer_name": "Globex Corp",
        "overdue_days": 10,
        "amount": 4999.0,
        "currency": "INR"
    }
    response = client.post("/api/v1/ai/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data
    assert "recommended_action" in data
    assert "personalized_draft" in data
