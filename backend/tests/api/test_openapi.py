from fastapi.testclient import TestClient


def test_errors_are_documented_as_problem_json(client: TestClient) -> None:
    spec = client.get("/api/v1/openapi.json").json()
    conflict = spec["paths"]["/api/v1/bookings"]["post"]["responses"]["409"]
    assert list(conflict["content"]) == ["application/problem+json"]
    schema = conflict["content"]["application/problem+json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/Problem"}
    assert "Problem" in spec["components"]["schemas"]
