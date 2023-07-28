from pydantic import BaseModel
from .main import ExtendableModelMeta


class ExtendableBaseModel(BaseModel, metaclass=ExtendableModelMeta):
    """Base class for extendable pydantic models."""

    pass
