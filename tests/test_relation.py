"""Test relations."""
from pydantic.main import BaseModel

from extendable_pydantic import ExtendableModelMeta


def test_model_relation(test_registry):
    class Coordinate(BaseModel, metaclass=ExtendableModelMeta):
        lat = 0.1
        lng = 10.1

    class Person(BaseModel, metaclass=ExtendableModelMeta):
        name: str
        coordinate: Coordinate

    class ExtendedCoordinate(Coordinate, extends=Coordinate):
        country: str = None

    test_registry.init_registry()
    ClsPerson = test_registry[Person.__xreg_name__]
    # check that the behaviour is the same for all the definitions
    # of the same model...
    classes = Person, ClsPerson
    for cls in classes:
        person = cls(
            name="test",
            coordinate={"lng": 5.0, "lat": 4.2, "country": "belgium"},
        )
        coordinate = person.coordinate
        assert isinstance(coordinate, Coordinate)
        # sub schema are stored into the definition property
        definitions = ClsPerson.schema().get("definitions", {})
        assert "Coordinate" in definitions
        coordinate_properties = definitions["Coordinate"].get("properties", {}).keys()
        assert {"lat", "lng", "country"} == set(coordinate_properties)
