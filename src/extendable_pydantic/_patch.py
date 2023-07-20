#  type: ignore
# ruff: noqa: E402

# The following 2 lines are required to prevent import error if others dependecies
# are not yet available into the python path when this file is loaded.
# This should be done by default unless the Python interpreter was started
# with the -S flag. It's at least required when this lib is deployed into odoo.sh
import site

site.main()


try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

import wrapt
from extendable import context
from pydantic import TypeAdapter

from .utils import all_identical, resolve_annotation


def _resolve_model_fields_annotation(model_fields):
    registry = context.extendable_registry.get()
    if registry:
        for field in model_fields:
            field_info = field.field_info
            new_type = resolve_annotation(field_info.annotation)
            if not all_identical(field_info.annotation, new_type):
                field_info.annotation = new_type
                field._type_adapter = TypeAdapter(Annotated[new_type, field_info])
    return model_fields


@wrapt.when_imported("fastapi.openapi.utils")
def hook_fastapi_openapi_utils(utils):
    # This method is used by fastapi to build the fields definition for all
    # the routes. We need to replace it with a wrapper that will replace
    # in the annotation any class that has been extended with the extended
    # class.
    # These definitions are used by fastapi to build the openapi schema.
    def _get_fields_from_routes_wrapper(wrapped, instance, args, kwargs):
        all_fields = wrapped(*args, **kwargs)
        _resolve_model_fields_annotation(all_fields)
        return all_fields

    wrapt.wrap_function_wrapper(
        utils, "get_fields_from_routes", _get_fields_from_routes_wrapper
    )


@wrapt.when_imported("fastapi.utils")
def hook_fastapi_utils(utils):
    # This method is used by fastapi to build the fields definition for all
    # the routes used to parse the request and to build the response.
    # This method is called a first time when the modules where the routes
    # are defined are imported. At this time the registry is not yet
    # initialized.
    # This method is then called every time a route is added to an app.
    # At this time the registry must be initialized. (it's the case
    # with the odoo.addons.fastapi module)
    def _create_response_field_wrapper(wrapped, instance, args, kwargs):
        field = wrapped(*args, **kwargs)
        _resolve_model_fields_annotation([field])
        return field

    wrapt.wrap_function_wrapper(
        utils, "create_response_field", _create_response_field_wrapper
    )
