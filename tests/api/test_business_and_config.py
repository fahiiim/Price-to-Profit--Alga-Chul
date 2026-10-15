from fastapi.testclient import TestClient

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json()["status"] == "ok"
    assert client.get("/health/ready").json() == {"status": "ready", "database": "ok"}


def test_app_config_has_defaults(client: TestClient) -> None:
    body = client.get("/v1/app-config").json()
    assert body["maintenance_mode"] is False
    assert body["minimum_app_version"] == "1.0.0"


def test_business_is_seeded_from_platform_defaults(client: TestClient) -> None:
    body = client.get("/v1/business").json()
    assert body["currency"] == "AED"
    assert body["tax_rate_percent"] == "5.00"
    assert body["hourly_rate"] == "180.00"
    assert body["logo_url"] is None
    assert "logo_path" not in body


def test_update_business(client: TestClient) -> None:
    response = client.patch(
        "/v1/business",
        json={"business_name": "Amna Hair Studio", "hourly_rate": "200"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["business_name"] == "Amna Hair Studio"
    assert body["hourly_rate"] == "200.00"


def test_business_rejects_bad_values(client: TestClient) -> None:
    response = client.patch("/v1/business", json={"business_name": None})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "business_rule_violation"

    response = client.patch("/v1/business", json={"tax_rate_percent": "150"})
    assert response.json()["error"]["code"] == "validation_error"

    response = client.patch(
        "/v1/business", json={"deposit_mode": "percent", "deposit_value": "150"}
    )
    assert response.json()["error"]["code"] == "business_rule_violation"


def test_logo_upload_download_and_delete(client: TestClient) -> None:
    upload = client.put(
        "/v1/business/logo", files={"file": ("logo.png", PNG_BYTES, "image/png")}
    )
    assert upload.status_code == 200
    assert upload.json()["logo_url"] == "/v1/business/logo"

    download = client.get("/v1/business/logo")
    assert download.status_code == 200
    assert download.content == PNG_BYTES

    assert client.delete("/v1/business/logo").status_code == 204
    assert client.get("/v1/business/logo").status_code == 404


def test_logo_validation(client: TestClient) -> None:
    wrong_type = client.put(
        "/v1/business/logo", files={"file": ("logo.gif", b"GIF89a", "image/gif")}
    )
    assert wrong_type.status_code == 415

    fake_png = client.put(
        "/v1/business/logo", files={"file": ("logo.png", b"not an image", "image/png")}
    )
    assert fake_png.status_code == 415

    too_large = client.put(
        "/v1/business/logo",
        files={"file": ("logo.png", PNG_BYTES + b"\x00" * 2_000, "image/png")},
    )
    assert too_large.status_code == 413
