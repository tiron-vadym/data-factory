from typing import List
from datetime import date
from starlette.status import HTTP_201_CREATED

from fastapi import APIRouter, Depends, UploadFile, File, Response, Query
from sqlalchemy.orm import Session
import pandas as pd

from app import crud, schemas, models
from dependencies import get_db

router = APIRouter()


@router.get("/user_credits/{user_id}", response_model=List[schemas.CreditInfo])
def user_credits(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_credits(db, user_id=user_id)


@router.post("/plans_insert", response_model=str)
async def plans_insert(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    contents = await file.read()
    df = pd.read_excel(contents)

    categories = db.query(models.Dictionary).all()
    category_map = {category.name: category.id for category in categories}
    df["category_id"] = df["category"].map(category_map)
    df = df.drop(columns=["category"])

    records = df.to_dict(orient="records")
    plans = [schemas.PlanInsert(**record) for record in records]
    crud.insert_plans(db, plans)

    return Response(
        content="Plans successfully inserted",
        status_code=HTTP_201_CREATED
    )


@router.get("/plans_performance", response_model=List[schemas.PlanPerformance])
def plans_performance(
        target_date: date = Query(default=date.today()),
        db: Session = Depends(get_db)
):
    return crud.get_plan_performance(db, target_date=target_date)


@router.get("/year_performance", response_model=List[schemas.YearPerformance])
def year_performance(year: int, db: Session = Depends(get_db)):
    return crud.get_year_performance(db, year=year)
