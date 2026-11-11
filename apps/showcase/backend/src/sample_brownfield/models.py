"""Core billing domain entities shared across legacy gateway modules."""

from pydantic import BaseModel, Field


class CustomerAccount(BaseModel):
    account_id: str
    legal_name: str
    credit_limit_eur: float = Field(ge=0.0)


class InvoiceRecord(BaseModel):
    invoice_id: str
    account_id: str
    amount_eur: float = Field(gt=0.0)
    status: str = "pending"


class TriageResult(BaseModel):
    invoice_id: str
    priority: str
    summary: str
