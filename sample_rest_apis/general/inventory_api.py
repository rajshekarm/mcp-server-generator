from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


app = FastAPI(
    title="Warehouse Inventory API",
    description="Search products and manage warehouse stock.",
    version="1.0.0",
)


class Product(BaseModel):
    sku: str
    name: str
    category: str
    unit_price: float
    quantity: int
    warehouse: str


class StockAdjustment(BaseModel):
    quantity_change: int = Field(description="Positive to add stock, negative to remove it")
    reason: str = Field(min_length=3, max_length=200)


class StockAdjustmentResult(BaseModel):
    sku: str
    previous_quantity: int
    new_quantity: int
    reason: str


PRODUCTS: dict[str, Product] = {
    "LAPTOP-001": Product(
        sku="LAPTOP-001",
        name="Developer Laptop",
        category="computers",
        unit_price=1499.00,
        quantity=12,
        warehouse="Chicago",
    ),
    "MONITOR-002": Product(
        sku="MONITOR-002",
        name="27-inch Monitor",
        category="displays",
        unit_price=349.00,
        quantity=30,
        warehouse="Austin",
    ),
    "KEYBOARD-003": Product(
        sku="KEYBOARD-003",
        name="Mechanical Keyboard",
        category="accessories",
        unit_price=129.00,
        quantity=50,
        warehouse="Chicago",
    ),
}


@app.get("/health", operation_id="inventory_health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products", response_model=list[Product], operation_id="search_products")
def search_products(
    category: str | None = Query(default=None),
    warehouse: str | None = Query(default=None),
    availability: Literal["all", "in_stock", "out_of_stock"] = "all",
) -> list[Product]:
    products = list(PRODUCTS.values())

    if category:
        products = [p for p in products if p.category.lower() == category.lower()]
    if warehouse:
        products = [p for p in products if p.warehouse.lower() == warehouse.lower()]
    if availability == "in_stock":
        products = [p for p in products if p.quantity > 0]
    elif availability == "out_of_stock":
        products = [p for p in products if p.quantity == 0]

    return products


@app.get("/products/{sku}", response_model=Product, operation_id="get_product")
def get_product(sku: str) -> Product:
    product = PRODUCTS.get(sku.upper())
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {sku} was not found")
    return product


@app.post(
    "/products/{sku}/stock-adjustments",
    response_model=StockAdjustmentResult,
    operation_id="adjust_product_stock",
)
def adjust_product_stock(sku: str, adjustment: StockAdjustment) -> StockAdjustmentResult:
    product = PRODUCTS.get(sku.upper())
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {sku} was not found")

    new_quantity = product.quantity + adjustment.quantity_change
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Adjustment would make stock negative")

    previous_quantity = product.quantity
    product.quantity = new_quantity
    return StockAdjustmentResult(
        sku=product.sku,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        reason=adjustment.reason,
    )
