from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_rbac_permission_matrix():
    checks = [
        ("GET", "/api/patients/raw", "token-bob", 403),
        ("GET", "/api/patients/raw", "token-alice", 200),
        ("GET", "/api/patients/anonymized", "token-bob", 200),
        ("GET", "/api/metrics/aggregated", "token-carol", 200),
        ("GET", "/api/metrics/aggregated", "token-dave", 403),
        ("DELETE", "/api/patients/abc123", "token-bob", 403),
        ("DELETE", "/api/patients/abc123", "token-alice", 200),
    ]

    for method, path, token, expected_status in checks:
        response = client.request(
            method,
            path,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == expected_status


def test_missing_token_is_401():
    response = client.get("/api/patients/raw")
    assert response.status_code == 401
