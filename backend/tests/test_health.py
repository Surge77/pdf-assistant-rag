from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_reports_service_status():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["services"]["vector_store"] in {"ready", "missing"}
    assert payload["services"]["ollama"] in {"ready", "unreachable"}
    assert payload["models"]["llm"] == "mistral:latest"
