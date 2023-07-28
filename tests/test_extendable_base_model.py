from typing import Generic, List, TypeVar

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from extendable_pydantic import ExtendableBaseModel

from .conftest import skip_not_supported_version_for_generics


def test_model_relation(test_registry):
    class MyModel(ExtendableBaseModel):
        x: str

        def test(self) -> str:
            return "base"

    class MyModelExtended(MyModel, extends=True):
        y: str

        def test(self) -> str:
            return super().test() + " extended"

    class MyModelInherited(MyModel):
        z: str

        def test(self) -> str:
            return super().test() + " inherited"

    test_registry.init_registry()
    assert MyModel(x="a", y="b").test() == "base extended"
    assert MyModelInherited(x="a", y="b", z="c").test() == "base extended inherited"


def test_import_module(test_registry):
    from .modtest.base import Base

    test_registry.init_registry(["tests.modtest.base"])

    schema = Base.model_json_schema()
    assert schema is not None
    assert schema.get("title") == "Base"
    assert schema["properties"].keys() == {"x", "myList", "y"}

    assert Base(x="a", y="b", myList=[]).model_dump() == {
        "x": "a",
        "myList": [],
        "y": "b",
    }


@skip_not_supported_version_for_generics
def test_generics_of_extended_base_model(test_registry):
    """In this test we check that generics of extended works."""
    T = TypeVar("T")

    class SearchResult(ExtendableBaseModel, Generic[T]):
        total: int
        results: List[T]

    class Location(ExtendableBaseModel):
        kind: Literal["view", "bin"]
        my_list: List[str]

    class SearchLocationResult(SearchResult[Location]):
        pass

    class LocationExtended(Location, extends=True):
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
def test_generics_of_extended_base_model_import_module(test_registry):
    """In this test we check that generics of extended works."""
    from .modtest.generics import SearchLocationResult, Location

    test_registry.init_registry(["tests.modtest.generics"])

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
