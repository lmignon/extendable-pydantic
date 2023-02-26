#  type: ignore
import wrapt


@wrapt.when_imported("pydantic.schema")
def hook_pydantic_schema(schema):
    # This method is called by fastapi to get the schema of a model.
    # We need to replace it with a wrapper that will return the schema
    # of the assembled class instead of the base class to make the extendable
    # models work with fastapi.
    def _model_process_schema_wrapper(wrapped, instance, args, kwargs):
        model = args[0]
        if hasattr(model, "_get_assembled_cls"):
            model = model._get_assembled_cls()
            args = (model,) + args[1:]
        return wrapped(*args, **kwargs)

    wrapt.wrap_function_wrapper(
        schema, "model_process_schema", _model_process_schema_wrapper
    )


@wrapt.when_imported("fastapi.routing")
def hook_fastapi_routing(routing):
    # This method is called by fastapi to serialize the response of a route.
    # We need to replace it with a wrapper that will use the extended class
    # instead of the base class to serialize the response.
    def _serialize_response_wrapper(wrapped, instance, args, kwargs):
        field = kwargs["field"]
        if hasattr(field, "_get_assembled_cls"):
            field = field._get_assembled_cls()
            kwargs["field"] = field
        return wrapped(**kwargs)

    wrapt.wrap_function_wrapper(
        routing, "serialize_response", _serialize_response_wrapper
    )


@wrapt.when_imported("fastapi.utils")
def hook_fastapi_utils(utils):
    # This method is called by fastapi to create a new field from an existing
    # field when the field is used as a response model. The motivation is to
    # ensure that the response model is not modified by the route handler.
    # We need to replace it with a wrapper that will use the extended class
    # as new field instead of a clone of the base class. Semantically, we
    # still ensure that the response model is not modified by the route handler.
    # since we enforce the use of the expected response model.
    def _create_cloned_field_wrapper(wrapped, instance, args, kwargs):
        field = args[0]
        if hasattr(field.type_, "_get_assembled_cls"):
            return field
        return wrapped(*args, **kwargs)

    wrapt.wrap_function_wrapper(
        utils, "create_cloned_field", _create_cloned_field_wrapper
    )
