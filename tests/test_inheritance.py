"""Test model inheritance."""
from typing import List, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from pydantic import Field
from pydantic.main import BaseModel

from extendable_pydantic import ExtendableBaseModel
from extendable_pydantic import ExtendableModelMeta


def test_simple_inheritance(test_registry):
    class Location(BaseModel, metaclass=ExtendableModelMeta):
        lat: float = 0.1
        lng: float = 10.1

        def test(self) -> str:
            return "location"

    class ExtendedLocation(Location, extends=Location):
        name: str

        def test(self, return_super: bool = False) -> str:
            if return_super:
                return super().test()
            return "extended"

    test_registry.init_registry()

    ClsLocation = test_registry[Location.__xreg_name__]
    classes = Location, ExtendedLocation, ClsLocation
    for cls in classes:
        schema = cls.model_json_schema()
        properties = schema.get("properties", {}).keys()
        assert schema.get("title") == "Location"
        assert {"lat", "lng", "name"} == set(properties)
        location = cls(name="name", lng=5.0, lat=4.2)
        assert location.model_dump() == {"lat": 4.2, "lng": 5.0, "name": "name"}
        assert location.test() == "extended"
        assert location.test(return_super=True) == "location"


def test_composite_inheritance(test_registry):
    class Coordinate(BaseModel, metaclass=ExtendableModelMeta):
        lat: float = 0.1
        lng: float = 10.1

    class Name(BaseModel, metaclass=ExtendableModelMeta):
        name: str

    class Location(Coordinate, Name):
        pass

    test_registry.init_registry()
    ClsLocation = test_registry[Location.__xreg_name__]
    assert issubclass(ClsLocation, Coordinate)
    assert issubclass(ClsLocation, Name)

    # check that the behaviour is the same for all the definitions
    # of the same model...
    classes = Location, ClsLocation
    for cls in classes:
        properties = cls.model_json_schema().get("properties", {}).keys()
        assert {"lat", "lng", "name"} == set(properties)
        location = cls(name="name", lng=5.0, lat=4.2)
        assert location.model_dump() == {"lat": 4.2, "lng": 5.0, "name": "name"}


def test_inheritance_new_model(test_registry):
    class MyModel(BaseModel, metaclass=ExtendableModelMeta):
        value: int = 2

        def method(self):
            return self.value

    class DerivedModel(MyModel):  # no extends, I want two different models here
        value2: int = 3

        def method(self):
            return super().method() + self.value2

    test_registry.init_registry()
    assert DerivedModel().method() == 5

    ClsDerivedModel = test_registry[DerivedModel.__xreg_name__]
    assert ClsDerivedModel().method() == 5


def test_inheritance_new_model_2(test_registry):
    class MyModel(BaseModel, metaclass=ExtendableModelMeta):
        value: int = 2

        def method(self):
            return self.value

    class DerivedModel(MyModel):  # no extends, I want two different models here
        value2: int = 3

        def method(self):
            return super().method() + self.value2

    class MyModelExtended(MyModel, extends=MyModel):
        def method(self):
            return super().method() + 1

    test_registry.init_registry()
    assert DerivedModel().method() == 6

    ClsDerivedModel = test_registry[DerivedModel.__xreg_name__]
    assert ClsDerivedModel().method() == 6


def test_instance(test_registry):
    class Location(BaseModel, metaclass=ExtendableModelMeta):
        lat: float = 0.1
        lng: float = 10.1

    class ExtendedLocation(Location, extends=Location):
        name: str

    test_registry.init_registry()

    inst1 = Location.model_construct()
    inst2 = ExtendedLocation.model_construct()
    assert inst1.__class__ == inst2.__class__
    assert inst1.model_json_schema() == inst2.model_json_schema()


def test_issubclass(test_registry):
    """In this test we check that issublass is lenient when used with GenericAlias as
    with Enum declaration."""

    class Location(BaseModel, metaclass=ExtendableModelMeta):
        kind: Literal["view", "bin"]
        my_list: List[str]

    test_registry.init_registry()

    assert not issubclass(Literal["test"], Location)
    assert not issubclass(Literal, Location)

    schema = Location.model_json_schema()
    assert schema is not None


def test_nested_inherited_with_optional_not_required(test_registry):
    # In this test, the Event class defines a field `time` which is optional.
    # Moreover, since a default value is provided, the field is not required.
    # The test checks that the field remains not required when the nested extended
    # classes are resolved at registry initialization.
    class Location(ExtendableBaseModel):
        lat: float = 0.1
        lng: float = 10.1

    class Time(ExtendableBaseModel):
        hour: int

    class Event(ExtendableBaseModel):
        location: Location
        time: Optional[Time] = None

    test_registry.init_registry()

    data = {"location": {"lat": 12.3, "lng": 13.2}}
    event = Event(**data)

    assert event.location.lat == 12.3
    assert event.time is None

    schema = Event.model_json_schema()
    assert schema is not None
    assert schema["properties"]["time"]["default"] is None
    assert schema["required"] == ["location"]


def test_nested_inherited_with_field_info(test_registry):
    # This test is based on the previous one, but the field `time` is now annotated
    # with a FieldInfo object. We check that the FieldInfo is correctly preserved
    # when the nested extended classes are resolved at registry initialization.
    class Location(ExtendableBaseModel):
        lat: float = 0.1
        lng: float = 10.1

    class Time(ExtendableBaseModel):
        hour: int

    class Event(ExtendableBaseModel):
        location: Location
        time: Optional[Time] = Field(None, description="The time of the event.")

    test_registry.init_registry()

    data = {"location": {"lat": 12.3, "lng": 13.2}}
    event = Event(**data)

    assert event.location.lat == 12.3
    assert event.time is None

    schema = Event.model_json_schema()
    assert schema is not None
    assert schema["properties"]["time"]["description"] == "The time of the event."
    assert schema["properties"]["time"]["default"] is None
    assert schema["required"] == ["location"]
