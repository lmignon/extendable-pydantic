from typing import Generic, List, TypeVar
from extendable_pydantic import ExtendableBaseModel

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

T = TypeVar("T")


class SearchResult(ExtendableBaseModel, Generic[T]):
    total: int
    results: List[T]


class Location(ExtendableBaseModel):
    kind: Literal["view", "bin"]
    my_list: List[str]


class LocationExtended(Location, extends=True):
    name: str


class SearchLocationResult(SearchResult[Location]):
    pass
