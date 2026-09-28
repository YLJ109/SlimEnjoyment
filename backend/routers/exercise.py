"""运动路由：新增、列表、删除。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from pydantic import BaseModel, Field, ConfigDict

from database.db import get_db
from database.models import ExerciseRecord
from middleware.auth import get_current_user_id
from services.user_service import mark_checkin
from utils.common import resp, parse_date
from utils.exceptions import AppException

router = APIRouter(prefix="/api/v1/exercise", tags=["运动"])


class ExerciseAdd(BaseModel):
    record_date: str = Field(..., description="YYYY-MM-DD")
    exercise_type: str = Field(..., description="运动类型，如 跑步/游泳")
    duration: int = Field(..., gt=0, description="时长（分钟）")
    calorie_burn: float = Field(..., ge=0, description="消耗热量")


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    record_date: date
    exercise_type: str
    duration: int
    calorie_burn: float


@router.post("/add")
def add_exercise(
    body: ExerciseAdd,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """新增运动记录。"""
    rec = ExerciseRecord(
        user_id=user_id,
        record_date=parse_date(body.record_date),
        exercise_type=body.exercise_type,
        duration=body.duration,
        calorie_burn=body.calorie_burn,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    mark_checkin(db, user_id, parse_date(body.record_date))
    return resp(200, "success", ExerciseOut.model_validate(rec).model_dump())


@router.get("/list")
def list_exercise(
    date: str = Query(None, description="YYYY-MM-DD，指定则只返回当天记录；缺省返回全部"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出运动记录（按日期倒序）。

    传入 date 时只返回当天，供「今日运动」使用；否则返回该用户全部记录。
    """
    q = db.query(ExerciseRecord).filter(ExerciseRecord.user_id == user_id)
    if date:
        q = q.filter(ExerciseRecord.record_date == parse_date(date))
    recs = q.order_by(
        ExerciseRecord.record_date.desc(), ExerciseRecord.id.desc()
    ).all()
    return resp(200, "success", {
        "records": [ExerciseOut.model_validate(r).model_dump() for r in recs]
    })


@router.delete("/{record_id}")
def delete_exercise(
    record_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """删除运动记录。"""
    rec = db.query(ExerciseRecord).filter(
        ExerciseRecord.id == record_id, ExerciseRecord.user_id == user_id
    ).first()
    if not rec:
        raise AppException(404, "运动记录不存在")
    db.delete(rec)
    db.commit()
    return resp(200, "success", {"success": True})
