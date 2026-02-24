from __future__ import annotations

from fastapi import HTTPException, status


class DomainError(Exception):
    message: str = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message


class NotFoundError(DomainError):
    message = "Resource not found"


class UnauthorizedError(DomainError):
    message = "Unauthorized"


class ConflictError(DomainError):
    message = "Resource already exists"


class RateLimitError(DomainError):
    message = "Too many requests"


HTTP_ERROR_MAP: dict[type[DomainError], tuple[int, str]] = {
    NotFoundError: (status.HTTP_404_NOT_FOUND, "resource_not_found"),
    UnauthorizedError: (status.HTTP_401_UNAUTHORIZED, "unauthorized"),
    ConflictError: (status.HTTP_409_CONFLICT, "conflict"),
    RateLimitError: (status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited"),
}


def to_http_exception(error: DomainError) -> HTTPException:
    status_code, code = HTTP_ERROR_MAP.get(
        type(error), (status.HTTP_400_BAD_REQUEST, "bad_request")
    )
    return HTTPException(status_code=status_code, detail={"code": code, "message": error.message})
