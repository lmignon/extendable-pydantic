Rely on the pydantic public API to resolve extendable models.

As a result:

- the monkey patches of pydantic internals (type refs) are removed, as well as
  the ``extendable_pydantic_patcher.pth`` file and the dependency on ``wrapt``;
  fastapi is only patched to resolve the extendable models used as query,
  header or cookie parameters;
- the ``extendable_pydantic.utils`` module is removed.

This requires ``extendable > 1.3.0`` (the classes built by the registry keep
the qualified name of the original class).
