"""Shared fixtures: a fresh in-memory database and API client per test."""

import copy
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.registry import Base
from app.factory import create_app
from app.quotes.schemas import WORKED_EXAMPLE


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    settings = Settings(
        database_url="sqlite:///:memory:",
        media_dir=tmp_path / "media",
        max_logo_bytes=1_000,
    )
    application = create_app(settings)
    Base.metadata.create_all(application.state.engine)
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Signed-in-as-a-studio: creates a business and sends `X-Business-Id`."""
    with TestClient(app) as test_client:
        created = test_client.post(
            "/v1/businesses", json={"business_name": "Amna Hair Studio"}
        )
        assert created.status_code == 201, created.text
        test_client.headers["X-Business-Id"] = str(created.json()["id"])
        yield test_client


@pytest.fixture
def quote_payload() -> dict[str, Any]:
    """The worked example: total 2,104.00, profit 1,240.00."""
    return copy.deepcopy(WORKED_EXAMPLE)


@pytest.fixture
def created_quote(client: TestClient, quote_payload: dict[str, Any]) -> dict:
    response = client.post("/v1/quotes", json=quote_payload)
    assert response.status_code == 201, response.text
    return response.json()
