from typing import Generic, TypeVar

from extendable_pydantic import ExtendableBaseModel

try:
    from typing import Literal
except ImportError:
    from typing import Literal

T = TypeVar("T")


class SearchResult(ExtendableBaseModel, Generic[T]):
    total: int
    results: list[T]


class Location(ExtendableBaseModel):
    kind: Literal["view", "bin"]
    my_list: list[str]


class LocationExtended(Location, extends=True):
    name: str


class SearchLocationResult(SearchResult[Location]):
    pass
