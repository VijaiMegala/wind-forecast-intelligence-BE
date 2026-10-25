from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_configured_origin_is_allowed() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_unknown_origin_is_not_allowed() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://unknown.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
