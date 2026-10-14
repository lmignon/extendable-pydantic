[![CI](https://github.com/lmignon/pydantic-ext/actions/workflows/ci.yml/badge.svg)](https://github.com/lmignon/pydantic-ext/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/lmignon/pydantic-ext/branch/master/graph/badge.svg?token=Z9FWM57T14)](https://codecov.io/gh/lmignon/pydantic-ext)

# Extendable Pydantic

This addons provides a new type used to declare [Pydantic](https://pypi.org/project/pydantic/)
model as [Extendable](https://pypi.org/project/extendable/) class.

From release 1.0.0 it only supports Pydantic >= 2.0.0.


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

loc.model_dump() == {"lat": 12.3, "lng": 13.2, "name": "My Loc"}
#> True

loc.model_json_schema()
#> {'title': 'Location', 'type': 'object', 'properties': {'lat': {'title': 'Lat', 'default': 0.1, 'type': 'number'}, 'lng': {'title': 'Lng', 'default': 10.1, 'type': 'number'}, 'name': {'title': 'Name', 'type': 'string'}}, 'required': ['name']}
```

## Usage with FastAPI

Extendable models can be used as request and response models or as dependencies
of FastAPI routes. Any reference to an extendable model is resolved to the final
class of the current registry when pydantic builds the schema. Therefore, the
routes must be added to the application (`app.include_router(...)`) once the
registry is initialized.

## Development

`pip install -e .`

## Release

The version of the package is computed from the git tags (hatch-vcs) and the
changelog is built from the news fragments (towncrier).

* Each change worth mentioning into the changelog comes with a news fragment
  into the `news` directory: `news/<issue number>.<type>`, or
  `news/+<name>.<type>` for a change without issue, where `<type>` is one of
  `feature`, `bugfix`, `doc`, `removal` or `misc`.
* To release a new version, run the `release` workflow from the GitHub "Actions"
  tab and choose the part of the version to increase (`patch`, `minor` or
  `major`). Once the run is approved (required reviewers of the
  `release-approval` environment), the workflow updates `HISTORY.rst`, tags the
  release, publishes the package to PyPI and creates the GitHub release.
