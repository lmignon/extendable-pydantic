"""Test the initialization of a registry which is not the current one."""

import pytest
from extendable import context, registry

from extendable_pydantic import ExtendableBaseModel


@pytest.mark.parametrize("init_count", [1, 2])
def test_registry_initialized_before_being_the_current_one(test_registry, init_count):
    """Odoo initializes the registry (sometimes twice: the installed addons, then
    the tested addon) before setting it as the current registry."""

    class Partner(ExtendableBaseModel):
        name: str = ""

    class SaleOrderPartner(Partner):
        ref: str = ""

    class SaleOrder(ExtendableBaseModel):
        recipient: SaleOrderPartner | None = None

    class PartnerExt(Partner, extends=True):
        phone: str = ""

    reg = registry.ExtendableClassesRegistry()
    token = context.extendable_registry.set(None)
    try:
        for _ in range(init_count):
            reg.init_registry()
    finally:
        context.extendable_registry.reset(token)
    context.extendable_registry.set(reg)

    order = SaleOrder.model_validate({"recipient": {"name": "n", "phone": "p"}})
    # the nested model is an instance of the final class of the registry
    assert type(order.recipient) is reg[SaleOrderPartner.__xreg_name__]
    assert isinstance(order.recipient, Partner)
    assert order.recipient.phone == "p"
