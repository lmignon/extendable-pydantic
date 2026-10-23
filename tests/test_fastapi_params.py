"""Test extendable models used as query and header parameters of fastapi routes."""

from typing import Any

from extendable import context, registry
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.modfastapi import base, ext  # noqa: F401


def create_client(module_matchings: list[str]) -> TestClient:
    """Create an app into the context of a registry built from the given modules,
    as done for each database by the fastapi addon of odoo."""
    reg = registry.ExtendableClassesRegistry()
    context.extendable_registry.set(reg)
    reg.init_registry(module_matchings)
    app = FastAPI()
    app.include_router(base.router)
    return TestClient(app)


def get_parameter_names(client: TestClient, path: str) -> list[str]:
    operation = client.get("/openapi.json").json()["paths"][path]["get"]
    return [parameter["name"] for parameter in operation["parameters"]]


def test_query_model(test_registry):
    client = create_client(["tests.modfastapi.*"])
    assert get_parameter_names(client, "/search") == ["name", "tags"]
    response = client.get("/search", params={"name": "n", "tags": "a"})
    assert response.status_code == 200, response.text
    # a single value is parsed as a list since tags is a field of the model
    assert response.json() == {"name": "n", "tags": ["a"]}


def test_header_model(test_registry):
    client = create_client(["tests.modfastapi.*"])
    assert "x-token" in get_parameter_names(client, "/headers")
    response = client.get("/headers", headers={"x-token": "secret"})
    assert response.status_code == 200, response.text
    assert response.json()["x_token"] == "secret"


def test_registries_with_different_extensions(test_registry):
    """Each app uses the final classes of its own registry."""
    clients: dict[str, Any] = {}
    for name, module_matchings in (
        ("extended", ["tests.modfastapi.base", "tests.modfastapi.ext"]),
        ("not_extended", ["tests.modfastapi.base"]),
    ):
        clients[name] = (
            create_client(module_matchings),
            context.extendable_registry.get(),
        )
    for name, expected in (("extended", ["name", "tags"]), ("not_extended", ["name"])):
        client, reg = clients[name]
        context.extendable_registry.set(reg)
        assert get_parameter_names(client, "/search") == expected
