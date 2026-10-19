"""The forecasts endpoint."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from api_to_sqlite.api_docs import FILTERED_READ
from api_to_sqlite.cities.dao import CityDAO
from api_to_sqlite.database import Connection, get_connection
from api_to_sqlite.forecasts import service
from api_to_sqlite.forecasts.dao import ForecastDAO
from api_to_sqlite.forecasts.models import ForecastFilter, Page
from api_to_sqlite.forecasts.schemas import ForecastList

router = APIRouter(prefix="/v1/forecasts", tags=["forecasts"])


@router.get("", summary="List daily forecasts", responses=FILTERED_READ)
def list_forecasts(
    city: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: Connection = Depends(get_connection),
    cities: CityDAO = Depends(CityDAO),
    forecasts: ForecastDAO = Depends(ForecastDAO),
) -> ForecastList:
    """List daily forecasts, one page at a time."""
    filters = ForecastFilter(
        start_date=(start_date or date.today()).isoformat(),
        end_date=end_date.isoformat() if end_date else None,
        city=city,
    )
    return service.list_forecasts(
        conn, cities, forecasts, filters, Page(limit=limit, offset=offset)
    )
