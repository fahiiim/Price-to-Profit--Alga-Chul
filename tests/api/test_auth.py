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
        assert body["access_token"]
        assert body["refresh_token"]
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


def test_refresh_token_rotates_and_authenticates(app) -> None:
    with TestClient(app) as client:
        body = register(client, email="amna@glamstrands.ae", name="Amna Khan")
        first_access = body["access_token"]
        first_refresh = body["refresh_token"]

        response = client.post(
            "/v1/auth/refresh", json={"refresh_token": first_refresh}
        )
        assert response.status_code == 200, response.text
        renewed = response.json()
        assert renewed["access_token"] != first_access
        assert renewed["refresh_token"] != first_refresh
        assert renewed["user"]["email"] == "amna@glamstrands.ae"

        client.headers["Authorization"] = f"Bearer {renewed['access_token']}"
        me = client.get("/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["name"] == "Amna Khan"

        client.headers["Authorization"] = f"Bearer {first_access}"
        assert client.get("/v1/auth/me").status_code == 401


def test_refresh_token_invalid_or_logged_out(app) -> None:
    with TestClient(app) as client:
        body = register(client, email="amna@glamstrands.ae", name="Amna Khan")
        refresh_tok = body["refresh_token"]

        bad = client.post("/v1/auth/refresh", json={"refresh_token": "wrong-token"})
        assert bad.status_code == 401

        assert client.post("/v1/auth/logout").status_code == 204

        revoked = client.post("/v1/auth/refresh", json={"refresh_token": refresh_tok})
        assert revoked.status_code == 401


def test_delete_account_removes_user_and_revokes_token(app) -> None:
    with TestClient(app) as client:
        register(client, email="delete_me@example.com", name="To Delete")

        # Deleting account requires valid auth
        response = client.delete("/v1/auth/me")
        assert response.status_code == 204

        # Token is immediately revoked
        assert client.get("/v1/auth/me").status_code == 401

        # Cannot log in anymore
        login_res = client.post(
            "/v1/auth/login",
            json={"email": "delete_me@example.com", "password": TEST_PASSWORD},
        )
        assert login_res.status_code == 401

        # Email is freed up to register anew
        re_register = client.post(
            "/v1/auth/register",
            json={
                "email": "delete_me@example.com",
                "name": "Recreated",
                "password": TEST_PASSWORD,
            },
        )
        assert re_register.status_code == 201


def test_delete_account_cascades_business_and_data(
    client: TestClient, created_quote: dict
) -> None:
    quote_id = created_quote["id"]

    # Invoice the quote
    invoice_res = client.post(f"/v1/quotes/{quote_id}/invoice", json={})
    assert invoice_res.status_code == 201

    # Delete the account
    del_res = client.delete("/v1/auth/me")
    assert del_res.status_code == 204

    # Now verify all protected calls fail with 401
    assert client.get("/v1/auth/me").status_code == 401
    assert client.get("/v1/quotes").status_code == 401
    assert client.get("/v1/invoices").status_code == 401


def test_delete_account_alias_and_unauthorized(app) -> None:
    with TestClient(app) as client:
        # Unauthorized without Bearer token
        assert client.delete("/v1/auth/me").status_code == 401
        assert client.delete("/v1/auth/account").status_code == 401

        # Alias /account works with Bearer token
        register(client, email="alias@example.com", name="Alias User")
        assert client.delete("/v1/auth/account").status_code == 204
        assert client.get("/v1/auth/me").status_code == 401
