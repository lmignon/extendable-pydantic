"""A lib to define pydantic models extendable at runtime."""

from importlib.metadata import version
from importlib.util import find_spec

# shortcut to main used class
from .main import ExtendableModelMeta
from .models import ExtendableBaseModel, StrictExtendableBaseModel

__version__ = version("extendable_pydantic")

if find_spec("fastapi") is not None:
    # resolve the extendable models used as parameters of the fastapi routes
    from . import _fastapi  # noqa: F401
