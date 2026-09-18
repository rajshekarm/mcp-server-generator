from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


TicketStatus = Literal["open", "in_progress", "resolved"]
TicketPriority = Literal["low", "medium", "high", "critical"]

app = FastAPI(
    title="Customer Support API",
    description="Create, search, and update customer support tickets.",
    version="1.0.0",
)


class Ticket(BaseModel):
    ticket_id: str
    customer_email: str
    subject: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime


class CreateTicketRequest(BaseModel):
    customer_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    priority: TicketPriority = "medium"


class UpdateTicketStatusRequest(BaseModel):
    status: TicketStatus


TICKETS: dict[str, Ticket] = {
    "TKT-1001": Ticket(
        ticket_id="TKT-1001",
        customer_email="alex@example.com",
        subject="Unable to download invoice",
        description="The invoice download returns an error.",
        priority="high",
        status="open",
        created_at=datetime(2026, 9, 10, 14, 30, tzinfo=timezone.utc),
    ),
    "TKT-1002": Ticket(
        ticket_id="TKT-1002",
        customer_email="sam@example.com",
        subject="Update mailing address",
        description="Please update the mailing address on the account.",
        priority="low",
        status="resolved",
        created_at=datetime(2026, 9, 11, 9, 15, tzinfo=timezone.utc),
    ),
}


@app.get("/health", operation_id="support_health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tickets", response_model=list[Ticket], operation_id="search_tickets")
def search_tickets(
    status: TicketStatus | None = Query(default=None),
    priority: TicketPriority | None = Query(default=None),
    customer_email: str | None = Query(default=None),
) -> list[Ticket]:
    tickets = list(TICKETS.values())

    if status:
        tickets = [ticket for ticket in tickets if ticket.status == status]
    if priority:
        tickets = [ticket for ticket in tickets if ticket.priority == priority]
    if customer_email:
        tickets = [
            ticket
            for ticket in tickets
            if ticket.customer_email.lower() == customer_email.lower()
        ]

    return tickets


@app.get("/tickets/{ticket_id}", response_model=Ticket, operation_id="get_ticket")
def get_ticket(ticket_id: str) -> Ticket:
    ticket = TICKETS.get(ticket_id.upper())
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found")
    return ticket


@app.post(
    "/tickets",
    response_model=Ticket,
    status_code=201,
    operation_id="create_ticket",
)
def create_ticket(request: CreateTicketRequest) -> Ticket:
    ticket_id = f"TKT-{uuid4().hex[:8].upper()}"
    ticket = Ticket(
        ticket_id=ticket_id,
        customer_email=request.customer_email,
        subject=request.subject,
        description=request.description,
        priority=request.priority,
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    TICKETS[ticket_id] = ticket
    return ticket


@app.patch(
    "/tickets/{ticket_id}/status",
    response_model=Ticket,
    operation_id="update_ticket_status",
)
def update_ticket_status(ticket_id: str, request: UpdateTicketStatusRequest) -> Ticket:
    ticket = TICKETS.get(ticket_id.upper())
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found")

    ticket.status = request.status
    return ticket
