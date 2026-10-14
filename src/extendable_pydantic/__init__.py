"""A lib to define pydantic models extendable at runtime."""

from importlib.metadata import version

# shortcut to main used class
from .main import ExtendableModelMeta
from .models import ExtendableBaseModel, StrictExtendableBaseModel

__version__ = version("extendable_pydantic")
