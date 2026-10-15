"""Translate exceptions into the API's single error envelope.

Every error response has the shape::

    {"error": {"code": "...", "message": "...", "details": [...]}}
"""

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import ApplicationError
from app.pricing.errors import PricingError


def error_body(
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the JSON body shared by every error response."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


async def handle_application_error(_: Request, exc: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message),
    )


async def handle_pricing_error(_: Request, exc: PricingError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=error_body("pricing_error", str(exc)),
    )


async def handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {
            "location": [str(part) for part in error["loc"]],
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=error_body("validation_error", "The request is not valid.", details),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler to the application."""
    app.add_exception_handler(ApplicationError, handle_application_error)
    app.add_exception_handler(PricingError, handle_pricing_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
