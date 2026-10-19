"""Turn domain errors into application/problem+json answers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi.exceptions import RequestValidationError
from api_to_sqlite.database import DatabaseConnectionError
from api_to_sqlite.cities.exceptions import CityAlreadyExists, CityNotFound

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

    @app.exception_handler(CityNotFound)
    async def city_not_found(request: Request, error: CityNotFound) -> JSONResponse:
        return problem(
            request,
            404,
            "/problems/city-not-found",
            "City not found",
            str(error),
        )

    @app.exception_handler(CityAlreadyExists)
    async def city_already_exists(
        request: Request, error: CityAlreadyExists
    ) -> JSONResponse:
        return problem(
            request,
            409,
            "/problems/city-already-exists",
            "City already exists",
            str(error),
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'][1:])}: {item['msg']}"
            for item in error.errors()
        )
        return problem(
            request,
            422,
            "/problems/validation-error",
            "Validation error",
            problems,
        )
