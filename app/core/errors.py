"""Expected application failures.

Services raise these instead of `HTTPException`, so business code never depends
on the web framework. `app.core.handlers` translates them into HTTP responses.
"""

from http import HTTPStatus


class ApplicationError(Exception):
    """Base class for every expected, client-facing failure."""

    code: str = "application_error"
    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnauthorizedError(ApplicationError):
    """The request has no valid credentials."""

    code = "unauthorized"
    status_code = HTTPStatus.UNAUTHORIZED


class NotFoundError(ApplicationError):
    """The requested resource does not exist."""

    code = "not_found"
    status_code = HTTPStatus.NOT_FOUND


class ConflictError(ApplicationError):
    """The request clashes with the resource's current state."""

    code = "conflict"
    status_code = HTTPStatus.CONFLICT


class BusinessRuleError(ApplicationError):
    """The input is well formed but breaks a business rule."""

    code = "business_rule_violation"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class FileTooLargeError(ApplicationError):
    """An uploaded file is larger than the configured limit."""

    code = "file_too_large"
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE


class UnsupportedFileTypeError(ApplicationError):
    """An uploaded file has a content type the API does not accept."""

    code = "unsupported_file_type"
    status_code = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
