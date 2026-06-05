import pytest

import backend.app as backend_app
from backend.app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_predict_requires_url(client):
    response = client.post("/predict", json={})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_predict_trusts_google_ai_domain(client):
    response = client.post("/predict", json={"url": "https://ai.google"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["prediction"] == "legitimate"
    assert payload["source"] == "trusted_domain"


def test_predict_trusts_claude_domain(client):
    response = client.post("/predict", json={"url": "https://claude.ai/new"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["prediction"] == "legitimate"
    assert payload["source"] == "trusted_domain"


def test_mark_legitimate_adds_feedback(client, tmp_path, monkeypatch):
    feedback_path = tmp_path / "user_legitimate_feedback.csv"
    trusted_path = tmp_path / "trusted_legitimate_domains.csv"
    monkeypatch.setattr(backend_app, "USER_FEEDBACK_PATH", feedback_path)
    monkeypatch.setattr(backend_app, "TRUSTED_DOMAINS_PATH", trusted_path)

    url = "https://example-user-feedback.test/dashboard"
    response = client.post("/mark-legitimate", json={"url": url})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["label"] == "legitimate"
    assert payload["domain"] == "example-user-feedback.test"

    feedback_text = feedback_path.read_text(encoding="utf-8")
    trusted_text = trusted_path.read_text(encoding="utf-8")

    assert url in feedback_text
    assert "example-user-feedback.test" in trusted_text
