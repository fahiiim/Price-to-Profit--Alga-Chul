from fastapi.testclient import TestClient

HAIR_ITEM = {
    "kind": "hair",
    "name": "Russian tape-ins 20in",
    "category": "Tape-ins",
    "grams_per_pack": "100",
    "pack_price": "350",
}


def test_create_and_read_hair_item(client: TestClient) -> None:
    response = client.post("/v1/library", json=HAIR_ITEM)
    assert response.status_code == 201
    body = response.json()
    assert response.headers["Location"] == f"/v1/library/{body['id']}"
    assert body["cost_per_gram"] == "3.5000"

    fetched = client.get(f"/v1/library/{body['id']}").json()
    assert fetched["name"] == HAIR_ITEM["name"]


def test_kind_specific_fields_are_required(client: TestClient) -> None:
    response = client.post("/v1/library", json={"kind": "hair", "name": "No pack"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unrelated_fields_are_cleared(client: TestClient) -> None:
    item = client.post("/v1/library", json={**HAIR_ITEM, "unit_price": "99"}).json()
    assert item["unit_price"] is None


def test_list_filters_and_archive(client: TestClient) -> None:
    hair = client.post("/v1/library", json=HAIR_ITEM).json()
    client.post(
        "/v1/library",
        json={"kind": "service", "name": "Toning", "unit_price": "150"},
    )

    assert client.get("/v1/library").json()["total"] == 2
    assert client.get("/v1/library", params={"kind": "service"}).json()["total"] == 1
    assert client.get("/v1/library", params={"search": "tape"}).json()["total"] == 1

    client.patch(f"/v1/library/{hair['id']}", json={"is_archived": True})
    assert client.get("/v1/library").json()["total"] == 1
    listed = client.get("/v1/library", params={"include_archived": True}).json()
    assert listed["total"] == 2


def test_update_rejects_missing_required_field(client: TestClient) -> None:
    item = client.post("/v1/library", json=HAIR_ITEM).json()
    response = client.patch(f"/v1/library/{item['id']}", json={"kind": "service"})
    assert response.status_code == 422
    assert "unit_price" in response.json()["error"]["message"]


def test_delete_item(client: TestClient) -> None:
    item = client.post("/v1/library", json=HAIR_ITEM).json()
    assert client.delete(f"/v1/library/{item['id']}").status_code == 204
    response = client.get(f"/v1/library/{item['id']}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
