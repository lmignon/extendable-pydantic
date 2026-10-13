from __future__ import annotations

import inspect
import typing
import warnings
from typing import Any, Dict, List, Optional, cast, no_type_check

from extendable import context, main
from extendable.main import ExtendableMeta
from extendable.registry import ExtendableClassesRegistry, ExtendableRegistryListener
from pydantic import GetCoreSchemaHandler
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.main import BaseModel
from pydantic_core import CoreSchema

if typing.TYPE_CHECKING:
    AnyClassmethod = classmethod[Any, Any, Any]


def _get_final_cls(cls: Any) -> Any:
    """Return the class to use in place of the given one for the current registry.

    The final class is the one built by the registry by aggregating all
    the extensions of the given class. The given class is returned as is
    if there is no registry or if the class is not (yet) into the
    registry.
    """
    registry = context.extendable_registry.get()
    if registry is None:
        return cls
    return registry.get(cls.__xreg_name__, cls)


def _get_pydantic_core_schema(
    cls: type[BaseModel], source: Any, handler: GetCoreSchemaHandler
) -> CoreSchema:
    """Delegate the core schema of an extendable model to its final class.

    This hook is called by pydantic each time the schema of a model is
    generated, including when the model is used as type of a field into
    another model or into a TypeAdapter (e.g. by fastapi). Therefore,
    any reference to an extendable model always resolves to the final
    class from the current registry.
    """
    final_cls = _get_final_cls(cls)
    if source is cls and final_cls is not cls:
        return handler.generate_schema(final_cls)
    return handler(source)


class ExtendableModelMeta(ExtendableMeta, ModelMetaclass):
    @no_type_check
    @classmethod
    def _build_original_class(metacls, name, bases, namespace, **kwargs):
        if not main._registry_build_mode and BaseModel in bases:
            # we must wrap all the classmethod defined into pydantic.BaseModel
            metacls._wrap_pydantic_base_model_class_methods(namespace)
        namespace.setdefault(
            "__get_pydantic_core_schema__", classmethod(_get_pydantic_core_schema)
        )
        return ModelMetaclass.__new__(metacls, name, bases, namespace, **kwargs)

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

    @property
    def __signature__(cls) -> inspect.Signature:
        """The signature of the final class.

        The signature is used by tools like fastapi to know the
        parameters expected to create an instance of the class (e.g. when
        the class is used as a dependency). Since the instances are
        created from the final class, the signature must be the one of
        the final class. As a property defined on the metaclass, it takes
        precedence over the `__signature__` attribute set by pydantic on
        the class.
        """
        signature: inspect.Signature = _get_final_cls(cls).__xreg_signature__
        return signature

    @__signature__.setter
    def __signature__(cls, value: Any) -> None:
        # keep the signature set by pydantic on the class
        type.__setattr__(cls, "__xreg_signature__", value)

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


class RegistryListener(ExtendableRegistryListener):
    def on_registry_initialized(self, registry: ExtendableClassesRegistry) -> None:
        self.rebuild_models(registry)

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

    def rebuild_models(self, registry: ExtendableClassesRegistry) -> None:
        """Rebuild the schema of all the final models of the registry.

        The schemas built while the registry was being built can refer
        to classes that were not yet the final ones. All the schemas
        must be invalidated before rebuilding them. Otherwise, pydantic
        could reuse an outdated schema, validator or serializer of a sub
        model.
        """
        models = [
            cast(type[BaseModel], cls)
            for cls in registry._extendable_classes.values()
            if issubclass(type(cls), ExtendableModelMeta)
        ]
        for model in models:
            if "__pydantic_core_schema__" in model.__dict__:
                delattr(model, "__pydantic_core_schema__")
            model.__pydantic_complete__ = False
        for model in models:
            model.model_rebuild(force=True)


ExtendableClassesRegistry.listeners.append(RegistryListener())
