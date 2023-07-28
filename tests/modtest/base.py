from extendable_pydantic import ExtendableBaseModel


class Base(ExtendableBaseModel):
    x: str


class Base2(Base, extends=True):
    y: str
