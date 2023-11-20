from __future__ import annotations

import sys
import types
import typing
from itertools import zip_longest
from typing import Any, List, Optional

import typing_extensions
from extendable import context
from extendable.main import ExtendableMeta
from extendable.registry import ExtendableClassesRegistry
from typing_extensions import get_args, get_origin

try:
    from typing import _TypingBase  # type: ignore[attr-defined,unused-ignore]
except ImportError:
    from typing import _Final as _TypingBase  # type: ignore[attr-defined,unused-ignore]

if sys.version_info >= (3, 10):
    from typing import _UnionGenericAlias  # type: ignore[attr-defined,unused-ignore]


typing_base = _TypingBase
_EMPTY = object()


def all_identical(left: Optional[Any], right: Optional[Any]) -> bool:
    """Check that the items of `left` are the same objects as those in `right`.

    >>> a, b = object(), object()
    >>> all_identical([a, b, a], [a, b, a])
    True
    >>> all_identical([a, b, [a]], [a, b, [a]])  # new list object, while "equal" is not "identical"
    False

    Credit: Pydantic
    """
    # check that left and right are iterables
    if not isinstance(left, typing.Iterable) or not isinstance(right, typing.Iterable):
        return left is right
    for left_item, right_item in zip_longest(left, right, fillvalue=_EMPTY):
        if left_item is not right_item:
            return False
    return True


def resolve_annotation(
    type_: Any, registry: Optional[ExtendableClassesRegistry] = None
) -> Any:
    """Return type with all occurrences of subclass of `ExtendableModelMeta` keys
    recursively replaced with their assembled class.

    Args:
        type_: The class or generic alias.
        registry:

    Returns:
        A new type representing the basic structure of `type_`

        Example:
    ```py
    from typing import List, Tuple, Union

    replace_types(Tuple[str, Union[List[MyExtendale], float]], registry)
    #> Tuple[int, Union[List[MyExtendale._get_assembled_cls(registry)], float]]
    ```

    Credits: Inspired from pydantic._internal._generics.replace_types

    see (https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_generics.py#L257C5-L257C18)
    """
    registry = registry if registry else context.extendable_registry.get()

    type_args = get_args(type_)
    origin_type = get_origin(type_)

    if origin_type is typing_extensions.Annotated:
        annotated_type, *annotations = type_args
        annotated = resolve_annotation(annotated_type, registry)
        for annotation in annotations:
            annotated = typing_extensions.Annotated[annotated, annotation]
        return annotated

    # Having type args is a good indicator that this is a typing module
    # class instantiation or a generic alias of some sort.
    if type_args:
        resolved_type_args = tuple(
            resolve_annotation(arg, registry) for arg in type_args
        )
        if all_identical(type_args, resolved_type_args):
            # If all arguments are the same, there is no need to modify the
            # type or create a new object at all
            return type_
        if (
            origin_type is not None
            and isinstance(type_, typing_base)
            and not isinstance(origin_type, typing_base)
            and getattr(type_, "_name", None) is not None
        ):
            # In python < 3.9 generic aliases don't exist so any of these like `list`,
            # `type` or `collections.abc.Callable` need to be translated.
            # See: https://www.python.org/dev/peps/pep-0585
            origin_type = getattr(typing, type_._name)
        assert origin_type is not None
        # PEP-604 syntax (Ex.: list | str) is represented with a types.UnionType object that does not have __getitem__.
        # We also cannot use isinstance() since we have to compare types.
        if sys.version_info >= (3, 10) and origin_type is types.UnionType:  # noqa: E721
            return _UnionGenericAlias(origin_type, resolved_type_args)
        return origin_type[resolved_type_args]

    # We handle pydantic generic models separately as they don't have the same
    # semantics as "typing" classes or generic aliases

    if not origin_type and issubclass(type(type_), ExtendableMeta):
        final_type = type_._get_assembled_cls(registry)
        if final_type is not type_:
            final_type._resolve_submodel_fields(registry)
        return final_type

    # Handle special case for typehints that can have lists as arguments.
    # `typing.Callable[[int, str], int]` is an example for this.
    if isinstance(type_, (List, list)):
        resolved_list = [resolve_annotation(element, registry) for element in type_]
        if all_identical(type_, resolved_list):
            return type_
        return resolved_list

    return type_
