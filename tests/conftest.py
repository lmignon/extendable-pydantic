from extendable_pydantic import _patch  # noqa: F401
import pytest
import sys
from extendable import context, main, registry
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import Depends
from extendable_pydantic import ExtendableBaseModel


skip_not_supported_version_for_generics = pytest.mark.skipif(
    sys.version_info < (3, 8) or hasattr(sys, "pypy_translation_info"),
    reason="generics only supported for python 3.8 and above and is not "
    "supported on pypy",
)


@pytest.fixture
def test_registry() -> registry.ExtendableClassesRegistry:
    reg = registry.ExtendableClassesRegistry()
    initial_class_defs = main._extendable_class_defs_by_module
    try:
        main._extendable_class_defs_by_module = initial_class_defs.copy()
        token = context.extendable_registry.set(reg)
        yield reg
    finally:
        main._extendable_class_defs_by_module = initial_class_defs
        context.extendable_registry.reset(token)


@pytest.fixture
def test_fastapi(test_registry) -> TestClient:
    app = FastAPI()
    my_router = APIRouter()

    class TestRequest(ExtendableBaseModel):
        name: str = "rqst"

        def get_type(self) -> str:
            return "request"

    class TestResponse(ExtendableBaseModel):
        name: str = "resp"

        def get_type(self) -> str:
            return "response"

    @my_router.get("/")
    def get() -> TestResponse:
        """Get method."""
        resp = TestResponse(name="World")
        assert hasattr(resp, "id")
        return resp

    @my_router.post("/")
    def post(rqst: TestRequest) -> TestResponse:
        """Post method."""
        resp = TestResponse(**rqst.model_dump())
        assert hasattr(resp, "id")
        return resp

    @my_router.get("/extended")
    def get_with_params(rqst: Annotated[TestRequest, Depends()]) -> TestResponse:
        """Get method with parameters."""
        resp = TestResponse(**rqst.model_dump())
        assert hasattr(resp, "id")
        return resp

    class ExtendedTestRequest(TestRequest, extends=TestRequest):
        id: int = 1

    class ExtendedTestResponse(TestResponse, extends=TestResponse):
        id: int = 2

    test_registry.init_registry()

    app.include_router(my_router)

    with TestClient(app) as client:
        yield client
