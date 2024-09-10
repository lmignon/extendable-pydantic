"""Test forward refs resolution."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from extendable_pydantic import ExtendableModelMeta


def test_simple_forward_ref(test_registry):
    class A(BaseModel, metaclass=ExtendableModelMeta):
        attr: int
        child: Optional["A"] = None
        children: Optional[List["A"]] = None  # noqa: F821

    class AExt(A, extends=A):
        model_config = ConfigDict(from_attributes=True)
        val: str

    test_registry.init_registry()
    schema = A.model_json_schema()
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
    assert a.model_dump() == json_dict
    assert A.model_validate(a).model_dump() == json_dict
    assert AExt.model_validate(a).model_dump() == json_dict
