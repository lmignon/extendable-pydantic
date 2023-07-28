from extendable_pydantic import ExtendableBaseModel


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

    test_registry.init_registry(["tests.modtest.*"])
    assert Base(x="a", y="b").model_dump() == {"x": "a", "y": "b"}
