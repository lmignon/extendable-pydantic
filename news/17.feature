Add a new base class `StrictExtendableBaseModel`. This class is a subclass of
`ExtendableBaseModel` and enforces strict validation by forcing the revalidation
 of instances when the method `model_validate` is called and by ensuring that
 the values assignment is validated. This class is useful when you need to
 instantiate you model from a partial dictionary and you want to ensure that
 any value assignment taking place after the instantiation is validated.
