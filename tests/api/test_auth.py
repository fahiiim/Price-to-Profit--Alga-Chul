from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, register


def test_register_does_not_issue_a_token(app) -> None:
    with TestClient(app) as client:
        pending = client.post(
            "/v1/auth/register",
            json={
                "email": "amna@glamstrands.ae",
                "name": "Amna Khan",
                "password": TEST_PASSWORD,
            },
        )
        assert pending.status_code == 201, pending.text
        body = pending.json()
        assert "access_token" not in body
        assert body["otp"]
        assert client.get("/v1/auth/me").status_code == 401


def test_verify_otp_then_login(app) -> None:
    with TestClient(app) as client:
        body = register(client, email="amna@glamstrands.ae", name="Amna Khan")
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "amna@glamstrands.ae"
        assert body["user"]["email_verified"] is True

        me = client.get("/v1/auth/me")
        assert me.status_code == 200, me.text
        assert me.json()["name"] == "Amna Khan"


def test_login_before_otp_is_rejected(app) -> None:
    with TestClient(app) as client:
        client.post(
            "/v1/auth/register",
            json={
                "email": "amna@example.com",
                "name": "Amna",
                "password": TEST_PASSWORD,
            },
        )
        login = client.post(
            "/v1/auth/login",
            json={"email": "amna@example.com", "password": TEST_PASSWORD},
        )
        assert login.status_code == 422
        assert login.json()["error"]["code"] == "business_rule_violation"


def test_wrong_otp_is_rejected(app) -> None:
    with TestClient(app) as client:
        client.post(
            "/v1/auth/register",
            json={
                "email": "amna@example.com",
                "name": "Amna",
                "password": TEST_PASSWORD,
            },
        )
        response = client.post(
            "/v1/auth/verify-otp",
            json={"email": "amna@example.com", "otp": "000000"},
        )
        assert response.status_code == 422


def test_register_normalizes_email_and_rejects_verified_duplicates(app) -> None:
    with TestClient(app) as client:
        register(client, email="Amna@Example.COM", name="Amna")
        again = client.post(
            "/v1/auth/register",
            json={
                "email": "amna@example.com",
                "name": "Amna",
                "password": TEST_PASSWORD,
            },
        )
        assert again.status_code == 409
        assert again.json()["error"]["code"] == "conflict"


def test_login_wrong_password(app) -> None:
    with TestClient(app) as client:
        register(client, email="amna@example.com", name="Amna")
        response = client.post(
            "/v1/auth/login",
            json={"email": "amna@example.com", "password": "not-the-password"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_login_unknown_email(app) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/auth/login",
            json={"email": "nobody@example.com", "password": TEST_PASSWORD},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_resend_otp_issues_a_new_code(app) -> None:
    with TestClient(app) as client:
        first = client.post(
            "/v1/auth/register",
            json={
                "email": "amna@example.com",
                "name": "Amna",
                "password": TEST_PASSWORD,
            },
        ).json()
        second = client.post("/v1/auth/resend-otp", json={"email": "amna@example.com"})
        assert second.status_code == 200, second.text
        new_otp = second.json()["otp"]
        assert new_otp
        old = client.post(
            "/v1/auth/verify-otp",
            json={"email": "amna@example.com", "otp": first["otp"]},
        )
        if new_otp != first["otp"]:
            assert old.status_code == 422
        assert (
            client.post(
                "/v1/auth/verify-otp",
                json={"email": "amna@example.com", "otp": new_otp},
            ).status_code
            == 204
        )


def test_logout_revokes_the_token(app) -> None:
    with TestClient(app) as client:
        register(client)
        assert client.post("/v1/auth/logout").status_code == 204
        me = client.get("/v1/auth/me")
        assert me.status_code == 401


def test_protected_routes_require_auth(app) -> None:
    with TestClient(app) as client:
        assert client.get("/v1/business").status_code == 401
        assert client.get("/v1/quotes").status_code == 401
        assert client.get("/v1/app-config").status_code == 200
