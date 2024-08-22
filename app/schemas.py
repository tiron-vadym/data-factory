from datetime import date
from pydantic import BaseModel
from typing import Optional


class CreditInfo(BaseModel):
    issuance_date: date
    is_closed: bool
    issuance_amount: Optional[float] = None
    accrued_interest: Optional[float] = None
    actual_return_date: Optional[date] = None
    total_payments: Optional[float] = None
    return_date: Optional[date] = None
    overdue_days: Optional[int] = None
    principal_payments: Optional[float] = None
    interest_payments: Optional[float] = None


class PlanInsert(BaseModel):
    period: date
    sum: float
    category_name: str


class PlanPerformance(BaseModel):
    period: date
    category_name: str
    plan_amount: float
    actual_amount: float
    fulfillment_percentage: float


class YearPerformance(BaseModel):
    month: str
    year: int
    issuance_count: int
    issuance_plan_amount: float
    issuance_actual_amount: float
    issuance_fulfillment_percentage: float
    payment_count: int
    payment_plan_amount: float
    payment_actual_amount: float
    payment_fulfillment_percentage: float
    issuance_year_percentage: float
    payment_year_percentage: float
