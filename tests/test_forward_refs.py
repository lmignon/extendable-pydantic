"""Test forward refs resolution."""
from typing import List

from pydantic import BaseModel

from extendable_pydantic import ExtendableModelMeta


def test_simple_forward_ref(test_registry):
    class A(BaseModel, metaclass=ExtendableModelMeta):
        attr: int
        child: "A" = None
        children: List["A"] = None  # noqa: F821

        class Config:
            orm_mode = True

    class AExt(A, extends=A):
        val: str

    test_registry.init_registry()
    schema = A.schema()
    assert schema
    json_dict = {
        "attr": 1,
        "val": "v",
        "child": {"attr": 1, "val": "v", "child": None, "children": None},
        "children": [{"attr": 1, "val": "v", "child": None, "children": None}],
    }
    a = A(**json_dict)
    assert len(a.children) == 1
    assert a.child
    assert a.child.val == "v"
    assert a.dict() == json_dict
    assert A.from_orm(a).dict() == json_dict
    assert AExt.from_orm(a).dict() == json_dict
