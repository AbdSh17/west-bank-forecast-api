"""Plain objects of the cities package. No HTTP and no SQL here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NewCity:
    """A city that is not stored yet: its name and coordinates."""

    name: str
    latitude: float
    longitude: float
