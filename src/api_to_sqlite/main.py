"""The FastAPI app: startup, routers and error handlers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from api_to_sqlite.health.router import router as health_router
from fastapi import FastAPI

from api_to_sqlite.database import ConnectionManager
from api_to_sqlite.errors import register_error_handlers
from api_to_sqlite.cities.router import router as cities_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the pool at startup so a down database stops the server early."""
    with ConnectionManager().connection():
        pass
    yield


app = FastAPI(title="Weather API", lifespan=lifespan)
app.include_router(health_router)
app.include_router(cities_router)
register_error_handlers(app)
