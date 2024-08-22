from datetime import date
from typing import List

from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import models, schemas


def get_user_credits(db: Session, user_id: int):
    creds = db.query(models.Credit).filter(
        models.Credit.user_id == user_id
    ).all()
    if not creds:
        raise HTTPException(
            status_code=404,
            detail="User not found or no credits available"
        )

    results = []
    for credit in creds:
        credit_info = {
            "issuance_date": credit.issuance_date,
            "is_closed": credit.is_closed,
            "issuance_amount": credit.body,
            "accrued_interest": credit.percent
        }
        if credit.is_closed:
            credit_info.update({
                "actual_return_date": credit.actual_return_date,
                "total_payments": credit.total_payments
            })
        else:
            credit_info.update({
                "return_date": credit.return_date,
                "overdue_days": (date.today() - credit.return_date).days,
                "principal_payments": credit.body,
                "interest_payments": credit.percent / 100 * credit.body
            })
        results.append(schemas.CreditInfo(**credit_info))
    return results


def insert_plans(db: Session, plans: List[schemas.PlanInsert]):
    for plan in plans:
        if plan.period.day != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period {plan.period}. "
                       f"Must be the first day of the month."
            )

        if plan.sum is None:
            raise HTTPException(
                status_code=400,
                detail=f"Sum for period {plan.period} "
                       f"and category {plan.category_id} cannot be empty"
            )

        existing_plan = db.query(models.Plan).filter(
            models.Plan.period == plan.period,
            models.Plan.category_id == plan.category_id
        ).first()
        if existing_plan:
            raise HTTPException(status_code=400,
                                detail=f"Plan for period {plan.period} and "
                                       f"category {plan.category_id}"
                                       f" already exists")

        db_plan = models.Plan(
            period=plan.period,
            category_id=plan.category_id,
            sum=plan.sum
        )
        db.add(db_plan)
    db.commit()


def get_plan_performance(
        db: Session,
        target_date: date
) -> List[schemas.PlanPerformance]:
    start_of_month = date(target_date.year, target_date.month, 1)

    plans = db.query(models.Plan).filter(
        models.Plan.period.between(start_of_month, target_date)
    ).all()

    results = []

    for plan in plans:
        actual_amount = 0

        if plan.category.name == "видача":
            creds = db.query(models.Credit).filter(
                models.Credit.issuance_date.between(
                    start_of_month,
                    target_date
                )
            ).all()
            actual_amount = sum(credit.body for credit in creds)

        elif plan.category.name == "збір":
            payments = db.query(models.Payment).filter(
                models.Payment.payment_date.between(
                    start_of_month,
                    target_date
                )
            ).all()
            actual_amount = sum(payment.sum for payment in payments)

        fulfillment_percentage = round(
            (actual_amount / plan.sum) * 100, 2
        ) if plan.sum else 0

        performance_data = schemas.PlanPerformance(
            period=plan.period,
            category_id=plan.category_id,
            plan_amount=plan.sum,
            actual_amount=actual_amount,
            fulfillment_percentage=fulfillment_percentage
        )

        results.append(performance_data)

    return results


MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}


def get_year_performance(
        db: Session,
        year: int
) -> List[schemas.YearPerformance]:
    monthly_performance = []
    total_issuance_amount = db.query(func.sum(models.Credit.body)).filter(
        extract("year", models.Credit.issuance_date) == year
    ).scalar() or 0
    total_payment_amount = db.query(func.sum(models.Payment.sum)).filter(
        extract("year", models.Payment.payment_date) == year
    ).scalar() or 0

    for month in range(1, 13):

        issuances = db.query(models.Credit).filter(
            extract("year", models.Credit.issuance_date) == year,
            extract("month", models.Credit.issuance_date) == month
        ).all()

        issuance_count = len(issuances)
        issuance_actual_amount = sum(credit.body for credit in issuances)

        issuance_plan = db.query(models.Plan).filter(
            extract("year", models.Plan.period) == year,
            extract("month", models.Plan.period) == month,
            models.Plan.category.has(name="видача")
        ).first()
        issuance_plan_amount = issuance_plan.sum if issuance_plan else 0

        issuance_fulfillment_percentage = round(
            (issuance_actual_amount / issuance_plan_amount) * 100, 2
        ) if issuance_plan_amount else 0

        issuance_year_percentage = round(
            (issuance_actual_amount / total_issuance_amount) * 100, 2
        ) if total_issuance_amount else 0

        payments = db.query(models.Payment).filter(
            extract("year", models.Payment.payment_date) == year,
            extract("month", models.Payment.payment_date) == month
        ).all()

        payment_count = len(payments)
        payment_actual_amount = sum(payment.sum for payment in payments)

        payment_plan = db.query(models.Plan).filter(
            extract("year", models.Plan.period) == year,
            extract("month", models.Plan.period) == month,
            models.Plan.category.has(name="збір")
        ).first()
        payment_plan_amount = payment_plan.sum if payment_plan else 0

        payment_fulfillment_percentage = round(
            (payment_actual_amount / payment_plan_amount) * 100, 2
        ) if payment_plan_amount else 0

        payment_year_percentage = round(
            (payment_actual_amount / total_payment_amount) * 100, 2
        ) if total_payment_amount else 0

        performance_data = schemas.YearPerformance(
            month=MONTH_NAMES[month],
            year=year,
            issuance_count=issuance_count,
            issuance_plan_amount=issuance_plan_amount,
            issuance_actual_amount=issuance_actual_amount,
            issuance_fulfillment_percentage=issuance_fulfillment_percentage,
            payment_count=payment_count,
            payment_plan_amount=payment_plan_amount,
            payment_actual_amount=payment_actual_amount,
            payment_fulfillment_percentage=payment_fulfillment_percentage,
            issuance_year_percentage=issuance_year_percentage,
            payment_year_percentage=payment_year_percentage
        )

        monthly_performance.append(performance_data)

    return monthly_performance
