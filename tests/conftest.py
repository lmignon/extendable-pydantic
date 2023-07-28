import pytest
import sys
from extendable import context, main, registry


skip_not_supported_version_for_generics = pytest.mark.skipif(
    sys.version_info < (3, 8) or hasattr(sys, "pypy_translation_info"),
    reason="generics only supported for python 3.8 and above and is not "
    "supported on pypy",
)


@pytest.fixture
def test_registry() -> registry.ExtendableClassesRegistry:
    reg = registry.ExtendableClassesRegistry()
    initial_class_defs = main._extendable_class_defs_by_module
    try:
        main._extendable_class_defs_by_module = initial_class_defs.copy()
        token = context.extendable_registry.set(reg)
        yield reg
    finally:
        main._extendable_class_defs_by_module = initial_class_defs
        context.extendable_registry.reset(token)
