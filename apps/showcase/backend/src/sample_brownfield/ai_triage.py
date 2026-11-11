"""Legacy Gemini dispute triage helper forwarding raw customer notes directly to the LLM."""

from config import GEMINI_MODEL
from models import InvoiceRecord, TriageResult

from nexus.ai import GeminiClient


def triage_invoice_dispute(invoice: InvoiceRecord, customer_note: str) -> TriageResult:
    client = GeminiClient(default_model=GEMINI_MODEL)
    prompt = f"Classify dispute for invoice {invoice.invoice_id}: {customer_note}"
    response = client.generate(prompt)
    return TriageResult(
        invoice_id=invoice.invoice_id,
        priority="high" if invoice.amount_eur > 5000 else "normal",
        summary=response.text[:160],
    )
