from __future__ import annotations

import typing
from typing import Any, Optional

try:
    pass  # type: ignore[attr-defined,unused-ignore]
except ImportError:
    pass  # type: ignore[attr-defined,unused-ignore]
from itertools import zip_longest

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
