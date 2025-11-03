from fastapi.testclient import TestClient
from api import app, MOCK_EXTERNAL_DATABASE

client = TestClient(app)

def test_track_existing_returns_200_and_persists():
    tracking_id = "TRACK0001"         # existe: tu generador crea TRACK0001..TRACK0100
    assert tracking_id in MOCK_EXTERNAL_DATABASE

    r = client.get(f"/api/v1/track/{tracking_id}")
    assert r.status_code == 200

    data = r.json()
    assert data["tracking_id"] == tracking_id
    assert "normalized_status" in data
    assert isinstance(data["current_location"]["latitude"], float)
    assert isinstance(data["current_location"]["longitude"], float)

    # ya debe quedar persistido para el endpoint interno
    r2 = client.get(f"/api/trackit/standard/{tracking_id}")
    assert r2.status_code == 200

def test_track_nonexistent_404():
    r = client.get("/api/v1/track/NOEXISTE9999")
    assert r.status_code == 404

def test_standard_without_prior_404():
    r = client.get("/api/trackit/standard/TRACK9999")
    assert r.status_code == 404

def test_webhook_missing_payload_400():
    r = client.post("/api/v1/webhook_simulator", json={})
    assert r.status_code == 400
