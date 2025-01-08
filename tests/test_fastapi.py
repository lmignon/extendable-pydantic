"""Test fastapi integration."""


def test_open_api_schema(test_fastapi):
    client = test_fastapi
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    schema = response.json()
    rqst_schema = schema["components"]["schemas"]["TestRequest"]
    assert rqst_schema["properties"] == {
        "name": {"title": "Name", "type": "string", "default": "rqst"},
        "id": {"title": "Id", "type": "integer", "default": 1},
    }
    resp_schema = schema["components"]["schemas"]["TestResponse"]
    assert resp_schema["properties"] == {
        "name": {"title": "Name", "type": "string", "default": "resp"},
        "id": {"title": "Id", "type": "integer", "default": 2},
    }

    extended_get_params = schema["paths"]["/extended"]["get"]["parameters"]
    assert len(extended_get_params) == 2
    assert extended_get_params[0] == {
        "in": "query",
        "name": "name",
        "required": False,
        "schema": {"title": "Name", "type": "string", "default": "rqst"},
    }
    assert extended_get_params[1] == {
        "in": "query",
        "name": "id",
        "required": False,
        "schema": {"title": "Id", "type": "integer", "default": 1},
    }


def test_extended_response(test_fastapi):
    """Test extended pydantic model as response."""
    client = test_fastapi
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "World", "id": 2}


def test_extended_request(test_fastapi):
    """Test extended pydantic model as json request."""
    client = test_fastapi
    response = client.post("/", json={"name": "Hello", "id": 3})
    assert response.status_code == 200
    assert response.json() == {"name": "Hello", "id": 3}


def test_extended_request_with_params(test_fastapi):
    """Test extended pydantic model as request with parameters."""
    client = test_fastapi
    response = client.get("/extended", params={"name": "echo", "id": 3})
    assert response.status_code == 200
    assert response.json() == {"name": "echo", "id": 3}
