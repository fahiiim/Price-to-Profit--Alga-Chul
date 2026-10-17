from fastapi.testclient import TestClient

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json()["status"] == "ok"
    assert client.get("/health/ready").json() == {"status": "ready", "database": "ok"}


def test_app_config_has_defaults(client: TestClient) -> None:
    body = client.get("/v1/app-config").json()
    assert body["maintenance_mode"] is False
    assert body["minimum_app_version"] == "1.0.0"


def test_create_business_copies_platform_defaults(client: TestClient) -> None:
    body = client.get("/v1/business").json()
    assert body["business_name"] == "Amna Hair Studio"
    assert body["currency"] == "AED"
    assert body["tax_rate_percent"] == "5.00"
    assert body["hourly_rate"] == "180.00"
    assert body["deposit_mode"] == "percent"
    assert body["deposit_value"] == "30.00"
    assert body["logo_url"] is None
    assert "logo_path" not in body


def test_first_launch_setup_creates_a_business(app) -> None:
    with TestClient(app) as anonymous:
        response = anonymous.post(
            "/v1/businesses",
            json={
                "business_name": "Glam Strands Studio",
                "owner_name": "Amna Khan",
                "tagline": "Luxury hair extensions · Dubai",
                "phone": "+971501234567",
                "email": "hello@glamstrands.ae",
                "instagram": "@glamstrands.dxb",
                "website": "https://glamstrands.ae",
                "address": "Jumeirah 1, Dubai, UAE",
                "currency": "AED",
                "tax_rate_percent": "5",
                "deposit_mode": "percent",
                "deposit_value": "30",
                "payment_link": "https://pay.glamstrands.ae/deposit",
                "quote_terms": "Deposit secures your appointment.",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["id"] >= 1
        assert body["business_name"] == "Glam Strands Studio"
        assert body["tagline"] == "Luxury hair extensions · Dubai"
        assert body["hourly_rate"] == "180.00"
        assert response.headers["location"] == f"/v1/businesses/{body['id']}"

        missing = anonymous.get("/v1/business")
        assert missing.status_code == 422

        anonymous.headers["X-Business-Id"] = str(body["id"])
        loaded = anonymous.get("/v1/business").json()
        assert loaded["owner_name"] == "Amna Khan"
        assert loaded["payment_link"] == "https://pay.glamstrands.ae/deposit"


def test_businesses_are_isolated(app) -> None:
    with TestClient(app) as api:
        first = api.post("/v1/businesses", json={"business_name": "Studio A"}).json()
        second = api.post("/v1/businesses", json={"business_name": "Studio B"}).json()

        api.headers["X-Business-Id"] = str(first["id"])
        created = api.post(
            "/v1/library",
            json={
                "kind": "fee",
                "name": "A only",
                "unit_price": "10",
            },
        )
        assert created.status_code == 201, created.text

        api.headers["X-Business-Id"] = str(second["id"])
        listed = api.get("/v1/library").json()
        assert listed["total"] == 0
        assert api.get(f"/v1/library/{created.json()['id']}").status_code == 404

        studios = api.get("/v1/admin/businesses").json()
        assert studios["total"] == 2


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
