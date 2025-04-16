"""Test Union."""

import sys
from typing import Union, Any, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from pydantic import Tag, Discriminator
from pydantic.main import BaseModel

from extendable_pydantic import ExtendableModelMeta

from pytest import fixture


@fixture
def model_union_base_models():
    class Coordinate(
        BaseModel,
        metaclass=ExtendableModelMeta,
        revalidate_instances="always",
        validate_assignment=True,
    ):
        lat: float = 0.1
        lng: float = 10.1

    class CoordinateWithCountry(Coordinate):
        country: str = None

    def _test_discriminate_coordinate_type(v: Any) -> Optional[str]:
        if isinstance(v, CoordinateWithCountry):
            return "coordinate_with_country"
        if isinstance(v, Coordinate):
            return "coordinate"
        if isinstance(v, dict):
            if "country" in v:
                return "coordinate_with_country"
            if "lat" in v:
                return "coordinate"
        return None

    class Person(
        BaseModel,
        metaclass=ExtendableModelMeta,
        revalidate_instances="always",
        validate_assignment=True,
    ):
        name: str
        coordinate: Optional[
            Annotated[
                Union[
                    Annotated[Coordinate, Tag("coordinate")],
                    Annotated[CoordinateWithCountry, Tag("coordinate_with_country")],
                ],
                Discriminator(_test_discriminate_coordinate_type),
            ]
        ] = None

    return Person, Coordinate, CoordinateWithCountry


@fixture
def model_union_models(model_union_base_models):
    Person, Coordinate, CoordinateWithCountry = model_union_base_models

    class ExtendedCoordinate(Coordinate, extends=Coordinate):
        state: str = None

    class ExtendedCoordinateWithCountry(
        CoordinateWithCountry, extends=CoordinateWithCountry
    ):
        currency: str = None

    return (
        Person,
        Coordinate,
        ExtendedCoordinate,
        CoordinateWithCountry,
        ExtendedCoordinateWithCountry,
    )


def test_model_union(model_union_models, test_registry):

    (
        Person,
        Coordinate,
        ExtendedCoordinate,
        CoordinateWithCountry,
        _ExtendedCoordinateWithCountry,
    ) = model_union_models
    test_registry.init_registry()
    ClsPerson = test_registry[Person.__xreg_name__]
    # check that the behaviour is the same for all the definitions
    # of the same model...
    classes = Person, ClsPerson
    for cls in classes:
        person = cls(
            name="test",
            coordinate={
                "lng": 5.0,
                "lat": 4.2,
                "country": "belgium",
                "state": "brussels",
                "currency": "euro",
            },
        )
        coordinate = person.coordinate
        assert isinstance(coordinate, CoordinateWithCountry)
        person = cls(
            name="test",
            coordinate={"lng": 5.0, "lat": 4.2, "state": "brussels"},
        )
        coordinate = person.coordinate
        assert isinstance(coordinate, Coordinate)

        # sub schema are stored into the definition property
        definitions = ClsPerson.model_json_schema().get("$defs", {})
        assert "Coordinate" in definitions
        coordinate_properties = definitions["Coordinate"].get("properties", {}).keys()
        assert {"lat", "lng", "state"} == set(coordinate_properties)
        assert "CoordinateWithCountry" in definitions
        coordinate_with_country_properties = (
            definitions["CoordinateWithCountry"].get("properties", {}).keys()
        )
        assert {"lat", "lng", "country", "state", "currency"} == set(
            coordinate_with_country_properties
        )

    person = Person(
        name="test",
        coordinate=Coordinate(
            lat=5.0,
            lng=4.2,
            state="brussels",
        ),
    )
    assert isinstance(person.coordinate, Coordinate)
    assert isinstance(person.coordinate, ExtendedCoordinate)
    assert person.model_dump(mode="python") == {
        "name": "test",
        "coordinate": {"lat": 5.0, "lng": 4.2, "state": "brussels"},
    }

    person = Person(
        name="test",
        coordinate=ExtendedCoordinate(
            lat=5.0,
            lng=4.2,
            state="brussels",
        ),
    )
    assert isinstance(person.coordinate, Coordinate)
    assert isinstance(person.coordinate, ExtendedCoordinate)


def test_union_validate_on_assign(model_union_base_models, test_registry):
    # covers issue https://github.com/lmignon/extendable/issues/18
    Person, Coordinate, CoordinateWithCountry = model_union_base_models
    test_registry.init_registry()
    ClsPerson = test_registry[Person.__xreg_name__]
    # check that the behaviour is the same for all the definitions
    # of the same model...
    classes = Person, ClsPerson
    for cls in classes:
        person = cls(
            name="test",
        )
        person.coordinate = CoordinateWithCountry(
            lng=5.0, lat=4.2, country="belgium", state="brussels", currency="euro"
        )
        coordinate = person.coordinate
        assert isinstance(coordinate, CoordinateWithCountry)
        person = cls(
            name="test",
            coordinate={"lng": 5.0, "lat": 4.2, "state": "brussels"},
        )
        coordinate = person.coordinate
        assert isinstance(coordinate, Coordinate)
