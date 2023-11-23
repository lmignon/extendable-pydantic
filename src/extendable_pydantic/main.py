from __future__ import annotations

import inspect
import typing
import warnings
from typing import Any, Dict, List, Optional, cast, no_type_check

from extendable import context, main
from extendable.main import ExtendableMeta
from extendable.registry import ExtendableClassesRegistry, ExtendableRegistryListener

try:
    from typing import _TypingBase  # type: ignore[attr-defined,unused-ignore]
except ImportError:
    from typing import _Final as _TypingBase  # type: ignore[attr-defined,unused-ignore]

from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo
from pydantic.main import BaseModel

from .utils import all_identical, resolve_annotation

typing_base = _TypingBase


if typing.TYPE_CHECKING:
    AnyClassmethod = classmethod[Any, Any, Any]


class ExtendableModelMeta(ExtendableMeta, ModelMetaclass):
    __xreg_fields_resolved__: bool = False

    @no_type_check
    @classmethod
    def _build_original_class(metacls, name, bases, namespace, **kwargs):
        if not main._registry_build_mode and BaseModel in bases:
            # we must wrap all the classmethod defined into pydantic.BaseModel
            metacls._wrap_pydantic_base_model_class_methods(namespace)
            pass
        return ModelMetaclass.__new__(metacls, name, bases, namespace, **kwargs)

    @no_type_check
    @classmethod
    def _prepare_namespace(
        metacls, name, bases, namespace, extends=None, **kwargs
    ) -> Dict[str, Any]:
        namespace = super()._prepare_namespace(
            name=name, bases=bases, namespace=namespace, extends=extends, **kwargs
        )
        namespace["__xreg_fields_resolved__"] = False
        return namespace

    @no_type_check
    def __call__(cls, *args, **kwargs) -> "ExtendableMeta":
        """Create the aggregated class in place of the original class definition.

        This method called at instance creation. The resulted instance
        will be an instance of the aggregated class not an instance of
        the original class definition since this definition could have
        been extended.
        """
        is_aggregated = getattr(
            cls._is_aggregated_class, "default", cls._is_aggregated_class
        )
        if is_aggregated:
            return super().__call__(*args, **kwargs)
        return cls._get_assembled_cls()(*args, **kwargs)

    @classmethod
    def _wrap_pydantic_base_model_class_methods(
        metacls, namespace: Dict[str, Any]
    ) -> Dict[str, Any]:
        new_namespace = namespace
        from pydantic.warnings import PydanticDeprecationWarning

        with warnings.catch_warnings():
            # ignore warnings about deprecated methods into pydantic.BaseModel
            warnings.filterwarnings("ignore", category=PydanticDeprecationWarning)
            methods = inspect.getmembers(BaseModel, inspect.ismethod)
            for name, method in methods:
                if name.startswith("__"):
                    continue
                if name in namespace:
                    continue
                new_namespace[name] = metacls._wrap_class_method(
                    cast("AnyClassmethod", method), name
                )
        return new_namespace

    ###############################################################
    # concrete methods provided to the final class by the metaclass
    ###############################################################
    def _resolve_submodel_fields(
        cls, registry: Optional[ExtendableClassesRegistry] = None
    ) -> None:
        """Replace the original field type into the definition of the field by the one
        from the registry."""
        registry = registry if registry else context.extendable_registry.get()
        if cls.__xreg_fields_resolved__:
            return
        cls.__xreg_fields_resolved__ = True
        to_rebuild = False
        if issubclass(cls, BaseModel):
            for field_name, field_info in cast(BaseModel, cls).model_fields.items():
                new_type = resolve_annotation(field_info.annotation, registry)
                if not all_identical(field_info.annotation, new_type):
                    cast(BaseModel, cls).model_fields[
                        field_name
                    ] = FieldInfo.merge_field_infos(field_info, annotation=new_type)
                    to_rebuild = True
        if to_rebuild:
            delattr(cls, "__pydantic_core_schema__")
            cast(BaseModel, cls).model_rebuild(force=True)


class RegistryListener(ExtendableRegistryListener):
    def on_registry_initialized(self, registry: ExtendableClassesRegistry) -> None:
        self.resolve_submodel_fields(registry)

    def before_init_registry(
        self,
        registry: "ExtendableClassesRegistry",
        module_matchings: Optional[List[str]] = None,
    ) -> None:
        if module_matchings is not None:
            # ensure that the current module is loaded...
            # prepend the current module to the module_matchings
            if "extendable_pydantic" not in module_matchings:
                module_matchings.insert(0, "extendable_pydantic.models")

    def resolve_submodel_fields(self, registry: ExtendableClassesRegistry) -> None:
        for cls in registry._extendable_classes.values():
            if issubclass(type(cls), ExtendableModelMeta):
                cast(ExtendableModelMeta, cls)._resolve_submodel_fields(registry)


ExtendableClassesRegistry.listeners.append(RegistryListener())

from pydantic._internal import _generate_schema  # noqa: E402

initial_type_ref = _generate_schema.get_type_ref


def get_type_ref(
    type_: type[Any], args_override: tuple[type[Any], ...] | None = None
) -> str:
    type_ref: str = initial_type_ref(type_, args_override)
    # Ensure type_ref unicity for each extendable model
    if issubclass(type(type_), ExtendableModelMeta):
        module_name = getattr(type_, "__module__", "<No __module__>")
        type_ref = f"{module_name}.{type_.__name__}:{id(type_)}"
    return type_ref


_generate_schema.get_type_ref = get_type_ref
