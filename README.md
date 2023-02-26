[![CI](https://github.com/lmignon/pydantic-ext/actions/workflows/ci.yml/badge.svg)](https://github.com/lmignon/pydantic-ext/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/lmignon/pydantic-ext/branch/master/graph/badge.svg?token=Z9FWM57T14)](https://codecov.io/gh/lmignon/pydantic-ext)

# pydantic-ext

This addons provides a new type used to declare [Pydantic](https://pypi.org/project/pydantic/)
model as [Extendable](https://pypi.org/project/extendable/) class.

```python
from pydantic import BaseModel
from extendable_pydantic import ExtendableModelMeta
from extendable import context, registry

class Location(BaseModel, metaclass=ExtendableModelMeta):
    lat = 0.1
    lng = 10.1

class ExtendedLocation(Location, extends=Location):
    name: str

_registry = registry.ExtendableClassesRegistry()
context.extendable_registry.set(_registry)
_registry.init_registry()

loc = Location(**{"lat": 12.3, "lng": 13.2, "name": "My Loc"})

loc.dict() == {"lat": 12.3, "lng": 13.2, "name": "My Loc"}
#> True

loc.schema()
#> {'title': 'Location', 'type': 'object', 'properties': {'lat': {'title': 'Lat', 'default': 0.1, 'type': 'number'}, 'lng': {'title': 'Lng', 'default': 10.1, 'type': 'number'}, 'name': {'title': 'Name', 'type': 'string'}}, 'required': ['name']}
```

## Development

`pip install -e .`

Then, copy `extendable_pydantic_patcher.pth` to `$VIRTUAL_ENV/lib/python3.10/site-packages`.
