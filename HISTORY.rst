1.3.1 (2024-09-10)
==================

Bugfixes
--------

- Fixes compatibility issue with fastapi version >= 0.112.3 (`#20 <https://github.com/lmignon/extendable-pydantic/issues/20>`_)


1.3.0 (2023-11-23)
==================

Bugfixes
--------

- Fix problem with unresolved annotated types in the aggregated model.

  At the end of the registry building process, the registry contains the aggregated
  model. Each aggregated model is the result of the build of a new class based on
  a hierarchy of all the classes defined as 'extends' of the same base class. The
  order of the classes hierarchy is defined by the order in which the classes are
  loaded by the class loader or by a specific order defined by the developer when
  the registry is built.

  The last step of the build process is to resolve all the annotated types in the
  aggregated model and rebuild the pydantic schema validator. This step is necessary
  because when the developer defines a model, some fields can be annotated with a
  type that refers to a class that is an extendable class. It's therefore necessary
  to update the annotated type with the aggregated result of the specified
  extendable class and rebuild the pydantic schema validator to take into account
  the new annotated types.

  Prior to this commit, the resolution of the annotated types was not done in a
  recursive way and the rebuild of the pydantic schema validator was only done
  just after the resolution of an aggregated class. This means that if a class A
  is an extendable defining a fields annotated with a type that refers to a class
  B, and if the class B is an extendable class defining a field of type C,
  the annotated type of the field of the class A was resolved with the aggregated
  model of the class B but we didn't resolve th annotated type of the field ot type
  B with the aggregated model of the type C. Therefore when the pydantic schema
  validator was rebuilt after the resolution of the class A, if the class B was
  not yet resolved and therefore the pydantic schema validator was not rebuilt,
  the new schema validator for the class A was not correct because it didn't take
  into account the aggregated model of the class C nor the definition of extra
  fields of the aggregated model of the class B.

  This commit changes the resolution of the annotated types to be recursive. Therefore
  when the pydantic schema validator is rebuilt, we are sure that all referenced
  subtypes are resolved and defines a correct schema validator. In the
  same time, when an aggregated class is resolved, it's marked as resolved to avoid
  to resolve it again and rebuild the pydantic schema validator again for nothing.
  In addition to resolve the initial problem, this commit also improves
  the performance of the build process because schema validators rebuilds are
  done only once per aggregated class. (`#19 <https://github.com/lmignon/extendable-pydantic/issues/19>`_)


1.2.1 (2023-11-13)
==================

Bugfixes
--------

- From Pydantic 2.5.0 the FieldInfo class is no more available in the pydantic.main
  module. It's only available in the pydantic.fields module. The import from the
  pydantic.main module was a mistake since it relied on an transitive import from
  pydantic.fields to pydantic.main. This is no more the case in Pydantic 2.5.0. (`#18 <https://github.com/lmignon/extendable-pydantic/issues/18>`_)


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
