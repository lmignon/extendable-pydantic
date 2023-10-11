"""A lib to define pydantic models extendable at runtime."""

# shortcut to main used class
from .main import ExtendableModelMeta
from .models import ExtendableBaseModel
from .models import StrictExtendableBaseModel
from .version import __version__
