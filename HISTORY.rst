1.2.0 (2023-10-11)
==================

Features
--------

- Add a new base class `StrictExtendableBaseModel`. This class is a subclass of
  `ExtendableBaseModel` and enforces strict validation by forcing the revalidation
   of instances when the method `model_validate` is called and by ensuring that
   the values assignment is validated. This class is useful when you need to
   instantiate you model from a partial dictionary and you want to ensure that
   any value assignment taking place after the instantiation is validated. (`#17 <https://github.com/lmignon/extendable-pydantic/issues/17>`_)


1.1.1 (2023-09-19)
==================

Bugfixes
--------

- Preserves the original FieldInfo when resolving nested extended classes at
  registry initialization time. Before this change, when the registry was
  initialized, and a field referencing a nested class was encountered, only
  the annotated information was preserved not the additional information provided
  as default value. (`#15 <https://github.com/lmignon/extendable-pydantic/issues/15>`_)


1.1.0 (2023-07-28)
==================

Features
--------

- Add new class `ExtendableBaseModel` as base class for extendable pydantic models


1.0.1 (2023-07-26)
==================

Bugfixes
--------

- Remove unused code breaking compatibility with Pydantic>=2.1.0 (`#9 <https://github.com/lmignon/extendable-pydantic/issues/9>`_)


1.0.0 (2023-07-20)
==================

Features
--------

- Makes the module working with pydantic V2. Therefore from version 1.0.0 extendable_pydantic no more support pydantic V1. (`#7 <https://github.com/lmignon/extendable-pydantic/pull/7>`_)


Bugfixes
--------

- Pervent 'ModuleNotFoundError' when used on Odoo.sh (`#3 <https://github.com/lmignon/extendable-pydantic/issues/3>`_)
