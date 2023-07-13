from __future__ import annotations

import functools
import inspect
import sys
import typing
import types
from typing import Any, Dict, Optional, cast, no_type_check, List

import typing_extensions
from extendable import context, main
from extendable.main import ExtendableMeta
from extendable.registry import ExtendableClassesRegistry, ExtendableRegistryListener
from typing_extensions import get_args, get_origin

try:
    from typing import _TypingBase  # type: ignore[attr-defined,unused-ignore]
except ImportError:
    from typing import _Final as _TypingBase  # type: ignore[attr-defined,unused-ignore]

if sys.version_info >= (3, 10):
    from typing import _UnionGenericAlias  # type: ignore[attr-defined,unused-ignore]

from pydantic.main import BaseModel, FieldInfo

from .utils import all_identical

from pydantic._internal._model_construction import ModelMetaclass

typing_base = _TypingBase


class ExtendableModelMeta(ExtendableMeta, ModelMetaclass):
    @no_type_check
    @classmethod
    def _build_original_class(metacls, name, bases, namespace, **kwargs):
        if (
            not main._registry_build_mode and BaseModel in bases
        ):  # or GenericModel in bases:
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
        methods = inspect.getmembers(BaseModel, inspect.ismethod)
        for name, method in methods:
            func = method.__func__
            if name.startswith("__"):
                continue
            if name in namespace:
                continue

            @no_type_check
            def new_method(cls, *args, _method_name=None, _initial_func=None, **kwargs):
                # ensure that arggs and kwargs are conform to the
                # initial signature
                inspect.signature(_initial_func).bind(cls, *args, **kwargs)
                try:
                    cls = cls._get_assembled_cls()
                    return getattr(cls, _method_name)(*args, **kwargs)
                except KeyError:
                    # the class is not yet assembled, we call the original method
                    return _initial_func(cls, *args, **kwargs)

            new_method_def = functools.partial(
                new_method, _method_name=name, _initial_func=func
            )
            # preserve signature for IDE
            functools.update_wrapper(new_method_def, func)
            new_namespace[name] = classmethod(new_method_def)
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
        to_rebuild = False
        if issubclass(cls, BaseModel):
            type_namespace = cast(BaseModel, cls).__pydantic_parent_namespace__ or {}
            name_space = type_namespace.get("namespace", {})
            for field_name, annoted_type in name_space.get(
                "__annotations__", {}
            ).items():
                if issubclass(type(annoted_type), ExtendableModelMeta):
                    name_space["__annotations__"][
                        field_name
                    ] = annoted_type._get_assembled_cls(registry)
                    to_rebuild = True
            for field_name, field_info in cast(BaseModel, cls).model_fields.items():
                new_type = cls.resolve_annotation(field_info.annotation, registry)  # type: ignore[attr-defined]
                if not all_identical(field_info.annotation, new_type):
                    cast(BaseModel, cls).model_fields[
                        field_name
                    ] = FieldInfo.from_annotation(new_type)
                    to_rebuild = True
        if to_rebuild:
            delattr(cls, "__pydantic_core_schema__")
            cast(BaseModel, cls).model_rebuild(force=True)
            return

    def resolve_annotation(cls, type_: Any, registry: ExtendableClassesRegistry) -> Any:
        """Return type with all occurrences of subclass of `ExtendableModelMeta` keys
        recursively replaced with their assembled class.

        Args:
            type_: The class or generic alias.

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

        type_args = get_args(type_)
        origin_type = get_origin(type_)

        if origin_type is typing_extensions.Annotated:
            annotated_type, *annotations = type_args
            annotated = cls.resolve_annotation(annotated_type, registry)
            for annotation in annotations:
                annotated = typing_extensions.Annotated[annotated, annotation]
            return annotated

        # Having type args is a good indicator that this is a typing module
        # class instantiation or a generic alias of some sort.
        if type_args:
            resolved_type_args = tuple(
                cls.resolve_annotation(arg, registry) for arg in type_args
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
            if (
                sys.version_info >= (3, 10)
                and origin_type is types.UnionType  # noqa: E721
            ):
                return _UnionGenericAlias(origin_type, resolved_type_args)
            return origin_type[resolved_type_args]

        # We handle pydantic generic models separately as they don't have the same
        # semantics as "typing" classes or generic aliases

        if not origin_type and issubclass(type(type_), ExtendableModelMeta):
            return type_._get_assembled_cls(registry)

        # Handle special case for typehints that can have lists as arguments.
        # `typing.Callable[[int, str], int]` is an example for this.
        if isinstance(type_, (List, list)):
            resolved_list = [
                cls.resolve_annotation(element, registry) for element in type_
            ]
            if all_identical(type_, resolved_list):
                return type_
            return resolved_list

        return type_


class RegistryListener(ExtendableRegistryListener):
    def on_registry_initialized(self, registry: ExtendableClassesRegistry) -> None:
        self.resolve_submodel_fields(registry)
        self.rebuild_models(registry)

    def rebuild_models(self, registry: ExtendableClassesRegistry) -> None:
        for cls in registry._extendable_classes.values():
            cast(BaseModel, cls).model_rebuild(force=True)

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
