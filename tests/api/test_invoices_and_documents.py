from typing import Any

from fastapi.testclient import TestClient


def _invoice(client: TestClient, quote_id: int) -> dict[str, Any]:
    response = client.post(f"/v1/quotes/{quote_id}/invoice")
    assert response.status_code == 201, response.text
    return response.json()


def test_invoice_locks_the_quote(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    invoice = _invoice(client, created_quote["id"])
    assert invoice["number"] == "INV-0001"
    assert invoice["status"] == "unpaid"
    assert invoice["amount_due"] == "2104.00"
    assert len(invoice["lines"]) == 5

    quote = client.get(f"/v1/quotes/{created_quote['id']}").json()
    assert quote["status"] == "invoiced"
    assert quote["invoice_id"] == invoice["id"]

    edit = client.patch(f"/v1/quotes/{created_quote['id']}", json={"title": "x"})
    assert edit.status_code == 409
    again = client.post(f"/v1/quotes/{created_quote['id']}/invoice")
    assert again.status_code == 409
    delete_quote = client.delete(f"/v1/quotes/{created_quote['id']}")
    assert delete_quote.status_code == 409


def test_payment_status_updates_amounts(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    invoice = _invoice(client, created_quote["id"])
    url = f"/v1/invoices/{invoice['id']}/status"

    deposit = client.patch(url, json={"status": "deposit_paid"}).json()
    assert deposit["amount_paid"] == "600.00"
    assert deposit["amount_due"] == "1504.00"

    paid = client.patch(url, json={"status": "paid"}).json()
    assert paid["amount_due"] == "0.00"
    assert paid["paid_at"] is not None


def test_due_date_before_issue_date_is_rejected(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    response = client.post(
        f"/v1/quotes/{created_quote['id']}/invoice",
        json={"issue_date": "2026-10-15", "due_date": "2026-10-01"},
    )
    assert response.status_code == 422


def test_declined_quote_cannot_be_invoiced(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    client.patch(
        f"/v1/quotes/{created_quote['id']}/status", json={"status": "declined"}
    )
    response = client.post(f"/v1/quotes/{created_quote['id']}/invoice")
    assert response.status_code == 409


def test_deleting_invoice_unlocks_quote(
    client: TestClient, created_quote: dict[str, Any]
) -> None:
    invoice = _invoice(client, created_quote["id"])
    assert client.delete(f"/v1/invoices/{invoice['id']}").status_code == 204

    quote = client.get(f"/v1/quotes/{created_quote['id']}").json()
    assert quote["status"] == "accepted"
    assert quote["invoice_id"] is None
    assert _invoice(client, created_quote["id"])["number"] == "INV-0002"


def test_list_invoices(client: TestClient, created_quote: dict[str, Any]) -> None:
    _invoice(client, created_quote["id"])
    page = client.get("/v1/invoices", params={"search": "sara"}).json()
    assert page["total"] == 1
    assert page["items"][0]["client_name"] == "Sara Ahmed"
    assert client.get("/v1/invoices", params={"status": "paid"}).json()["total"] == 0


def test_pdfs_render(client: TestClient, created_quote: dict[str, Any]) -> None:
    client.patch("/v1/business", json={"payment_link": "https://pay.example.com/x"})
    quote_id = created_quote["id"]

    for url in (f"/v1/quotes/{quote_id}/pdf", f"/v1/quotes/{quote_id}/cost-sheet/pdf"):
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")

    invoice = _invoice(client, quote_id)
    response = client.get(
        f"/v1/invoices/{invoice['id']}/pdf", params={"download": True}
    )
    assert response.content.startswith(b"%PDF")
    assert response.headers["content-disposition"] == (
        'attachment; filename="INV-0001.pdf"'
    )


def test_pdf_for_missing_quote_is_404(client: TestClient) -> None:
    assert client.get("/v1/quotes/999/pdf").status_code == 404
