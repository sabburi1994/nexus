"""Legacy FastAPI HTTP routes depending on models and ai_triage."""

from ai_triage import triage_invoice_dispute
from fastapi import FastAPI
from models import InvoiceRecord, TriageResult

app = FastAPI(title="Legacy Enterprise Billing Gateway")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "legacy-billing"}


@app.post("/api/v1/invoices")
def create_invoice(invoice: InvoiceRecord) -> InvoiceRecord:
    return invoice


@app.post("/api/v1/disputes/triage")
def run_dispute_triage(invoice: InvoiceRecord, note: str) -> TriageResult:
    return triage_invoice_dispute(invoice, note)
