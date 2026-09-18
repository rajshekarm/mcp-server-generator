from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


ServiceLevel = Literal["ground", "two_day", "overnight"]

app = FastAPI(
    title="Shipping and Tracking API",
    description="Calculate shipping quotes and track parcels.",
    version="1.0.0",
)


class ShippingQuoteRequest(BaseModel):
    origin_postal_code: str = Field(min_length=5, max_length=10)
    destination_postal_code: str = Field(min_length=5, max_length=10)
    weight_kg: float = Field(gt=0, le=100)
    service_level: ServiceLevel = "ground"


class ShippingQuote(BaseModel):
    service_level: ServiceLevel
    amount: float
    currency: str
    estimated_business_days: int


class TrackingEvent(BaseModel):
    date: date
    location: str
    description: str


class ShipmentTracking(BaseModel):
    tracking_number: str
    status: str
    estimated_delivery: date
    events: list[TrackingEvent]


SHIPMENTS: dict[str, ShipmentTracking] = {
    "SHIP-1001": ShipmentTracking(
        tracking_number="SHIP-1001",
        status="in_transit",
        estimated_delivery=date(2026, 9, 18),
        events=[
            TrackingEvent(
                date=date(2026, 9, 15),
                location="Chicago, IL",
                description="Package received by carrier",
            ),
            TrackingEvent(
                date=date(2026, 9, 16),
                location="Indianapolis, IN",
                description="Package departed distribution center",
            ),
        ],
    ),
    "SHIP-1002": ShipmentTracking(
        tracking_number="SHIP-1002",
        status="delivered",
        estimated_delivery=date(2026, 9, 14),
        events=[
            TrackingEvent(
                date=date(2026, 9, 14),
                location="Austin, TX",
                description="Delivered",
            )
        ],
    ),
}


@app.get("/health", operation_id="shipping_health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/service-levels", operation_id="list_shipping_service_levels")
def list_shipping_service_levels() -> list[dict[str, str | int]]:
    return [
        {"code": "ground", "description": "Economy ground shipping", "days": 5},
        {"code": "two_day", "description": "Two-business-day shipping", "days": 2},
        {"code": "overnight", "description": "Next-business-day shipping", "days": 1},
    ]


@app.post(
    "/quotes",
    response_model=ShippingQuote,
    operation_id="calculate_shipping_quote",
)
def calculate_shipping_quote(request: ShippingQuoteRequest) -> ShippingQuote:
    rates: dict[ServiceLevel, tuple[float, int]] = {
        "ground": (4.50, 5),
        "two_day": (9.50, 2),
        "overnight": (18.00, 1),
    }
    rate_per_kg, estimated_days = rates[request.service_level]
    amount = round(6.00 + request.weight_kg * rate_per_kg, 2)

    return ShippingQuote(
        service_level=request.service_level,
        amount=amount,
        currency="USD",
        estimated_business_days=estimated_days,
    )


@app.get(
    "/shipments/{tracking_number}",
    response_model=ShipmentTracking,
    operation_id="track_shipment",
)
def track_shipment(tracking_number: str) -> ShipmentTracking:
    shipment = SHIPMENTS.get(tracking_number.upper())
    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail=f"Shipment {tracking_number} was not found",
        )
    return shipment
