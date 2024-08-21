from io import StringIO
from typing import List
from datetime import date

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd

from app import crud, schemas
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
    contents = contents.decode("utf-8")
    csv_file = StringIO(contents)
    df = pd.read_csv(csv_file, sep="\t")
    df["period"] = pd.to_datetime(df["period"], format="%d.%m.%Y").dt.date

    records = df.to_dict(orient="records")
    plans = [schemas.PlanInsert(**record) for record in records]
    crud.insert_plans(db, plans)

    return "Plans successfully inserted"


@router.get("/plans_performance", response_model=List[schemas.PlanPerformance])
def plans_performance(db: Session = Depends(get_db)):
    target_date = date.today()
    return crud.get_plan_performance(db, target_date=target_date)


@router.get("/year_performance", response_model=List[schemas.YearPerformance])
def year_performance(year: int, db: Session = Depends(get_db)):
    return crud.get_year_performance(db, year=year)
