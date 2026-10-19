"""Turn domain errors into application/problem+json answers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api_to_sqlite.database import DatabaseConnectionError

PROBLEM_JSON = "application/problem+json"
RETRY_AFTER_SECONDS = "2"


def problem(
    request: Request,
    status: int,
    problem_type: str,
    title: str,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build an RFC 9457 problem answer."""
    return JSONResponse(
        status_code=status,
        content={
            "type": problem_type,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
        },
        media_type=PROBLEM_JSON,
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Connect each domain error to its HTTP answer."""

    @app.exception_handler(DatabaseConnectionError)
    async def database_unavailable(
        request: Request, error: DatabaseConnectionError
    ) -> JSONResponse:
        return problem(
            request,
            503,
            "/problems/database-unavailable",
            "Database unavailable",
            "The database is not available right now. Try again shortly.",
            headers={"Retry-After": RETRY_AFTER_SECONDS},
        )
