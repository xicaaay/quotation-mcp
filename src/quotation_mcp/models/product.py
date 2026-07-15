"""Modelos de entrada y salida del catálogo de productos."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


ProductArea = Literal["DESIGN", "DEVELOPMENT"]
PricingType = Literal["PER_UNIT", "FIXED", "RECURRING"]
BillingPeriod = Literal["ONE_TIME", "MONTHLY", "QUARTERLY", "YEARLY"]
DeliveryUnit = Literal["BUSINESS_DAYS", "CALENDAR_DAYS", "WEEKS", "MONTHS"]


class ProductFilters(BaseModel):
    """Filtros estructurados permitidos para consultar productos."""

    area: ProductArea | None = None
    pricing_type: PricingType | None = None
    billing_period: BillingPeriod | None = None
    active_only: bool = True
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    delivery_unit: DeliveryUnit | None = None


class ProductSummary(BaseModel):
    """Representación segura y serializable de un producto."""

    id: str
    code: str
    name: str
    description: str | None
    area: str
    pricing_type: str
    base_price: Decimal
    currency: str
    unit_name: str
    billing_period: str
    estimated_delivery_value: int | None
    estimated_delivery_unit: str | None
    minimum_quantity: int
    is_active: bool
    display_order: int
