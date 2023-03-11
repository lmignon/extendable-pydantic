"""Test generics model inheritance."""
import sys
from typing import Generic, List, TypeVar

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import pytest
from pydantic.generics import GenericModel
from pydantic.main import BaseModel

from extendable_pydantic import ExtendableModelMeta

skip_not_supported_version_for_generics = pytest.mark.skipif(
    sys.version_info < (3, 8) or hasattr(sys, "pypy_translation_info"),
    reason="generics only supported for python 3.8 and above and is not "
    "supported on pypy",
)


@skip_not_supported_version_for_generics
def test_generics_of_extended(test_registry):
    """In this test we check that generics of extended works."""
    T = TypeVar("T")

    class SearchResult(GenericModel, Generic[T], metaclass=ExtendableModelMeta):
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

    schema = SearchLocationResult.schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/definitions/Location"
    assert schema["definitions"]["Location"]["properties"].keys() == {
        "kind",
        "my_list",
        "name",
    }
    result = SearchLocationResult(
        total=0,
        results=[Location(kind="view", my_list=["a", "b"], name="name")],
    )
    assert result.dict() == {
        "total": 0,
        "results": [{"kind": "view", "my_list": ["a", "b"], "name": "name"}],
    }


@skip_not_supported_version_for_generics
def test_extended_generics(test_registry):
    """In this test we check that extending a generics works."""
    T = TypeVar("T")

    class SearchResult(GenericModel, Generic[T], metaclass=ExtendableModelMeta):
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

    schema = SearchLocationResult.schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results", "offset"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/definitions/Location"
    assert schema["definitions"]["Location"]["properties"].keys() == {
        "kind",
        "my_list",
    }
    result = SearchLocationResult(
        offset=1,
        total=0,
        results=[Location(kind="view", my_list=["a", "b"])],
    )
    assert result.dict() == {
        "offset": 1,
        "total": 0,
        "results": [{"kind": "view", "my_list": ["a", "b"]}],
    }


@skip_not_supported_version_for_generics
def test_extended_generics_of_extended_model(test_registry):
    """In this test we check that the extension of a genrics of extended model
    workks."""
    T = TypeVar("T")

    class SearchResult(GenericModel, Generic[T], metaclass=ExtendableModelMeta):
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

    schema = SearchLocationResult.schema()
    assert schema is not None
    assert schema.get("title") == "SearchLocationResult"
    assert schema.get("properties", {}).keys() == {"total", "results", "offset"}
    assert schema["properties"]["results"]["items"]["$ref"] == "#/definitions/Location"
    assert schema["definitions"]["Location"]["properties"].keys() == {
        "kind",
        "my_list",
        "name",
    }
    result = SearchLocationResult(
        offset=1,
        total=0,
        results=[Location(kind="view", my_list=["a", "b"], name="name")],
    )
    assert result.dict() == {
        "offset": 1,
        "total": 0,
        "results": [{"kind": "view", "my_list": ["a", "b"], "name": "name"}],
    }
