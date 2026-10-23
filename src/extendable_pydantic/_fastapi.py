"""Resolve the extendable models used as parameters of the FastAPI routes.

FastAPI flattens the fields of a pydantic model used as query, header or cookie
parameters (e.g. ``Annotated[MyModel, Query()]``) from the ``model_fields`` of
the annotation, i.e. the original class of an extendable model: the fields added
by the extensions would be ignored by the OpenAPI schema and by the parsing of
the request.

The annotations of the parameters are therefore replaced by the final class of
the current registry when FastAPI analyzes the parameters of a route. FastAPI
builds the routes of an application into the context of its registry, so each
application uses the final classes of its own registry.
"""

from __future__ import annotations

from typing import Annotated, Any, get_args, get_origin

from fastapi.dependencies import utils

from .main import ExtendableModelMeta, _get_final_cls

_analyze_param = utils.analyze_param


def _resolve_annotation(annotation: Any) -> Any:
    """Return the annotation where an extendable model is replaced by its final
    class."""
    if get_origin(annotation) is Annotated:
        annotated_type, *metadata = get_args(annotation)
        resolved_type = _resolve_annotation(annotated_type)
        if resolved_type is annotated_type:
            return annotation
        # nested Annotated are flattened: Annotated[Annotated[T, a], b] is
        # Annotated[T, a, b]
        resolved_annotation = resolved_type
        for item in metadata:
            resolved_annotation = Annotated[resolved_annotation, item]
        return resolved_annotation
    if isinstance(annotation, ExtendableModelMeta):
        return _get_final_cls(annotation)
    return annotation


def analyze_param(*args: Any, **kwargs: Any) -> Any:
    if "annotation" in kwargs:
        kwargs["annotation"] = _resolve_annotation(kwargs["annotation"])
    return _analyze_param(*args, **kwargs)


utils.analyze_param = analyze_param
