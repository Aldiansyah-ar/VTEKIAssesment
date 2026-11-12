from decimal import Decimal
from src.schema import Invoice, LineItem, Party
from src.validator import validate


def _inv(**kw):
    base = dict(
        invoice_number="A1", issue_date_raw="01/01/2024",
        seller=Party(name="S"), client=Party(name="C"),
        line_items=[LineItem(no=1, description="x", quantity=Decimal("1"),
                             unit="pcs", unit_price=Decimal("100"),
                             net_worth=Decimal("100"), vat_rate=Decimal("10"),
                             gross_worth=Decimal("110"))],
        subtotal=Decimal("100"), tax_total=Decimal("10"),
        grand_total=Decimal("110"),
    )
    base.update(kw)
    return Invoice(**base)


def test_reconciliation_passes():
    review, warn = validate(_inv())
    assert review == []


def test_reconciliation_fails_when_grand_total_wrong():
    inv = _inv(grand_total=Decimal("999"))
    review, _ = validate(inv)
    assert any("reconcile" in r for r in review)