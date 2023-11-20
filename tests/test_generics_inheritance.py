"""Test generics model inheritance."""
from typing import Generic, List, TypeVar, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from pydantic.main import BaseModel

from extendable_pydantic import ExtendableModelMeta
from extendable_pydantic.models import ExtendableBaseModel

from .conftest import skip_not_supported_version_for_generics


def test_base():
    T = TypeVar("T")

    class SearchResult(BaseModel, Generic[T]):
        total: int
        results: List[T]

    class Location(BaseModel):
        kind: Literal["view", "bin"]
        my_list: List[str]

    class SearchLocationResult(SearchResult[Location]):
        pass

    schema = SearchLocationResult.model_json_schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/$defs/Location"


@skip_not_supported_version_for_generics
def test_generics_of_extended(test_registry):
    """In this test we check that generics of extended works."""
    T = TypeVar("T")

    class SearchResult(BaseModel, Generic[T], metaclass=ExtendableModelMeta):
        total: int
        results: List[T]

    class Location(BaseModel, metaclass=ExtendableModelMeta):
        kind: Literal["view", "bin"]
        my_list: List[str]

    class SearchLocationResult(SearchResult[Location]):
        pass

    class LocationExtended(Location, extends=Location):
        name: str

    test_registry.init_registry()

    schema = SearchLocationResult.model_json_schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/$defs/Location"
    assert schema["$defs"]["Location"]["properties"].keys() == {
        "kind",
        "my_list",
        "name",
    }
    result = SearchLocationResult(
        total=0,
        results=[Location(kind="view", my_list=["a", "b"], name="name")],
    )
    assert result.model_dump() == {
        "total": 0,
        "results": [{"kind": "view", "my_list": ["a", "b"], "name": "name"}],
    }


@skip_not_supported_version_for_generics
def test_extended_generics(test_registry):
    """In this test we check that extending a generics works."""
    T = TypeVar("T")

    class SearchResult(BaseModel, Generic[T], metaclass=ExtendableModelMeta):
        total: int
        results: List[T]

    class Location(BaseModel, metaclass=ExtendableModelMeta):
        kind: Literal["view", "bin"]
        my_list: List[str]

    class SearchLocationResult(SearchResult[Location]):
        pass

    class SearchResultExtended(SearchResult[T], Generic[T], extends=SearchResult[T]):
        offset: int

    test_registry.init_registry()

    schema = SearchLocationResult.model_json_schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results", "offset"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/$defs/Location"
    assert schema["$defs"]["Location"]["properties"].keys() == {
        "kind",
        "my_list",
    }
    result = SearchLocationResult(
        offset=1,
        total=0,
        results=[Location(kind="view", my_list=["a", "b"])],
    )
    assert result.model_dump() == {
        "offset": 1,
        "total": 0,
        "results": [{"kind": "view", "my_list": ["a", "b"]}],
    }


@skip_not_supported_version_for_generics
def test_generic_with_nested_extended(test_registry):
    T = TypeVar("T")

    class SearchResult(ExtendableBaseModel, Generic[T]):
        total: int
        results: List[T]

    class Level(ExtendableBaseModel):
        val: int

    class SearchLevelResult(SearchResult[Level]):
        pass

    class Level11(ExtendableBaseModel):
        val: int

    class Level1(ExtendableBaseModel):
        val: int
        level11: Optional[Level11]

    class Level11Extended(Level11, extends=True):
        name: str = "level11"

    class Level1Extended(Level1, extends=True):
        name: str = "level1"

    class LevelExtended(Level, extends=True):
        name: str = "level"
        level1: Optional[Level1]

    test_registry.init_registry()

    assert Level11(val=3).model_dump() == {"val": 3, "name": "level11"}

    item = SearchLevelResult(
        total=0,
        results=[Level(val=1, level1=Level1(val=2, level11=Level11(val=3)))],
    )
    assert item.model_dump() == {
        "total": 0,
        "results": [
            {
                "val": 1,
                "level1": {
                    "val": 2,
                    "level11": {
                        "val": 3,
                        "name": "level11",
                    },
                    "name": "level1",
                },
                "name": "level",
            }
        ],
    }


@skip_not_supported_version_for_generics
def test_extended_generics_of_extended_model(test_registry):
    """In this test we check that the extension of a genrics of extended model
    workks."""
    T = TypeVar("T")

    class SearchResult(BaseModel, Generic[T], metaclass=ExtendableModelMeta):
        total: int
        results: List[T]

    class Location(BaseModel, metaclass=ExtendableModelMeta):
        kind: Literal["view", "bin"]
        my_list: List[str]

    class SearchLocationResult(SearchResult[Location]):
        pass

    class SearchResultExtended(SearchResult[T], Generic[T], extends=SearchResult[T]):
        offset: int

    class LocationExtended(Location, extends=Location):
        name: str

    test_registry.init_registry()

    schema = SearchLocationResult.model_json_schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results", "offset"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/$defs/Location"
    assert schema["$defs"]["Location"]["properties"].keys() == {
        "kind",
        "my_list",
        "name",
    }
    result = SearchLocationResult(
        offset=1,
        total=0,
        results=[Location(kind="view", my_list=["a", "b"], name="name")],
    )
    assert result.model_dump() == {
        "offset": 1,
        "total": 0,
        "results": [{"kind": "view", "my_list": ["a", "b"], "name": "name"}],
    }
