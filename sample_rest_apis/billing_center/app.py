from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


InvoiceStatus = Literal["due", "paid", "overdue"]

app = FastAPI(
    title="Insurance BillingCenter API",
    description="Review policy billing accounts, invoices, and payments.",
    version="1.0.0",
)


class Invoice(BaseModel):
    invoice_id: str
    policy_number: str
    due_date: date
    amount: float
    status: InvoiceStatus


class BillingAccount(BaseModel):
    account_id: str
    customer_id: str
    policy_number: str
    balance: float
    next_payment_date: date | None
    payment_plan: Literal["monthly", "quarterly", "annual"]


class RecordPaymentRequest(BaseModel):
    amount: float = Field(gt=0, le=1_000_000)
    payment_method: Literal["bank_account", "credit_card", "debit_card"]
    reference: str = Field(min_length=3, max_length=100)


class PaymentReceipt(BaseModel):
    receipt_id: str
    account_id: str
    amount: float
    remaining_balance: float
    payment_method: str
    reference: str


ACCOUNTS: dict[str, BillingAccount] = {
    "BILL-1001": BillingAccount(
        account_id="BILL-1001",
        customer_id="CUS-1001",
        policy_number="POL-1001",
        balance=200,
        next_payment_date=date(2026, 10, 1),
        payment_plan="monthly",
    ),
    "BILL-1002": BillingAccount(
        account_id="BILL-1002",
        customer_id="CUS-1002",
        policy_number="POL-1002",
        balance=450,
        next_payment_date=date(2026, 10, 15),
        payment_plan="quarterly",
    ),
}

INVOICES: dict[str, Invoice] = {
    "INV-1001": Invoice(
        invoice_id="INV-1001",
        policy_number="POL-1001",
        due_date=date(2026, 10, 1),
        amount=100,
        status="due",
    ),
    "INV-1002": Invoice(
        invoice_id="INV-1002",
        policy_number="POL-1002",
        due_date=date(2026, 10, 15),
        amount=450,
        status="due",
    ),
}


def _find_account(account_id: str) -> BillingAccount:
    account = ACCOUNTS.get(account_id.upper())
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} was not found")
    return account


@app.get("/health", operation_id="billing_center_health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/billing-accounts",
    response_model=list[BillingAccount],
    operation_id="search_billing_accounts",
)
def search_billing_accounts(
    customer_id: str | None = Query(default=None),
    policy_number: str | None = Query(default=None),
) -> list[BillingAccount]:
    accounts = list(ACCOUNTS.values())
    if customer_id:
        accounts = [a for a in accounts if a.customer_id.upper() == customer_id.upper()]
    if policy_number:
        accounts = [a for a in accounts if a.policy_number.upper() == policy_number.upper()]
    return accounts


@app.get(
    "/billing-accounts/{account_id}",
    response_model=BillingAccount,
    operation_id="get_billing_account",
)
def get_billing_account(account_id: str) -> BillingAccount:
    return _find_account(account_id)


@app.get("/invoices", response_model=list[Invoice], operation_id="search_invoices")
def search_invoices(
    policy_number: str | None = Query(default=None),
    status: InvoiceStatus | None = Query(default=None),
) -> list[Invoice]:
    invoices = list(INVOICES.values())
    if policy_number:
        invoices = [i for i in invoices if i.policy_number.upper() == policy_number.upper()]
    if status:
        invoices = [i for i in invoices if i.status == status]
    return invoices


@app.post(
    "/billing-accounts/{account_id}/payments",
    response_model=PaymentReceipt,
    operation_id="record_payment",
)
def record_payment(account_id: str, request: RecordPaymentRequest) -> PaymentReceipt:
    account = _find_account(account_id)
    if request.amount > account.balance:
        raise HTTPException(status_code=409, detail="Payment exceeds account balance")

    account.balance = round(account.balance - request.amount, 2)
    return PaymentReceipt(
        receipt_id=f"RCT-{account.account_id.split('-')[1]}",
        account_id=account.account_id,
        amount=request.amount,
        remaining_balance=account.balance,
        payment_method=request.payment_method,
        reference=request.reference,
    )
