"""The health endpoints."""

from fastapi import APIRouter, Depends

from api_to_sqlite.api_docs import DATABASE_UNAVAILABLE
from api_to_sqlite.database import Connection, get_connection

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check that the process is up")
def health() -> dict:
    """Report that the process is up. No database call."""
    return {"status": "ok"}


@router.get(
    "/health/ready",
    summary="Check that the database answers",
    responses={**DATABASE_UNAVAILABLE},
)
def ready(conn: Connection = Depends(get_connection)) -> dict:
    """Report that the database answers."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    finally:
        cursor.close()
    return {"status": "ready"}
