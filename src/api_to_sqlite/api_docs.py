"""Shared descriptions of the error answers for the generated /docs page."""

from pydantic import BaseModel

PROBLEM_JSON = "application/problem+json"


class Problem(BaseModel):
    """The body of every error answer (RFC 9457)."""

    type: str
    title: str
    status: int
    detail: str
    instance: str


def _problem(
    status: int,
    description: str,
    type_: str,
    title: str,
    detail: str,
    instance: str,
    headers: dict | None = None,
) -> dict:
    """Build one entry for a route's responses argument."""
    entry = {
        "description": description,
        "content": {
            PROBLEM_JSON: {
                "schema": Problem.model_json_schema(),
                "example": {
                    "type": type_,
                    "title": title,
                    "status": status,
                    "detail": detail,
                    "instance": instance,
                },
            }
        },
    }
    if headers:
        entry["headers"] = headers
    return {status: entry}


CITY_NOT_FOUND = _problem(
    404,
    "No city has the requested name.",
    "/problems/city-not-found",
    "City not found",
    "No city named 'nowhere'.",
    "/v1/cities/nowhere",
)

CITY_ALREADY_EXISTS = _problem(
    409,
    "A city with this name exists already. Letter case is ignored.",
    "/problems/city-already-exists",
    "City already exists",
    "A city named 'Tulkarm' already exists.",
    "/v1/cities",
)

VALIDATION_ERROR = _problem(
    422,
    "A parameter or a body field is invalid.",
    "/problems/validation-error",
    "Validation error",
    "latitude: Input should be less than or equal to 90",
    "/v1/cities",
)

DATABASE_UNAVAILABLE = _problem(
    503,
    "The database is down, or no connection became free within 2 seconds.",
    "/problems/database-unavailable",
    "Database unavailable",
    "The database is not available right now. Try again shortly.",
    "/v1/cities",
    headers={
        "Retry-After": {
            "description": "Seconds to wait before trying again.",
            "schema": {"type": "string", "example": "2"},
        }
    },
)

FILTERED_READ = {**CITY_NOT_FOUND, **VALIDATION_ERROR, **DATABASE_UNAVAILABLE}
