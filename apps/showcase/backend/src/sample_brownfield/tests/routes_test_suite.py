"""Regression test suite covering HTTP routes in legacy billing gateway."""

from models import InvoiceRecord
from routes import create_invoice, health


def verify_legacy_health() -> None:
    res = health()
    assert res["status"] == "ok"


def verify_create_invoice() -> None:
    inv = InvoiceRecord(invoice_id="inv_01", account_id="acc_01", amount_eur=250.0)
    out = create_invoice(inv)
    assert out.invoice_id == "inv_01"
