from extendable_pydantic import ExtendableBaseModel
from typing import List


class Base(ExtendableBaseModel):
    x: str
    myList: List[str]


class Base2(Base, extends=True):
    y: str
