"""AI 路由：食物识别、食谱生成、对话、每日复盘。"""
import os
import uuid
import asyncio
import logging
from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from database.db import get_db
from middleware.auth import get_current_user_id
from schemas.ai import (
    RecognizeResponse, FoodItem, PlanRequest, PlanResponse, ChatRequest,
    ChatResponse, DailyReviewResponse,
)
from services.ai_service import ai_service
from services.auth_service import get_current_user
from services.user_service import get_user_ai_settings, build_cfg
from utils.common import resp, parse_date, today
from utils.exceptions import AppException
from sqlalchemy import func
from database.models import DietRecord, AiDietPlan
import json

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])
logger = logging.getLogger("ai.recognize")


def _cfg(db, user_id: int, cap: str, default_model: str) -> dict:
    """读取用户某套能力的调用配置。"""
    row = get_user_ai_settings(db, user_id)
    return build_cfg(row, cap, default_model)


# 常见图片格式的文件头（magic bytes），用于真实类型校验，避免仅靠扩展名被绕过
_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",          # JPEG
    b"\x89PNG\r\n\x1a\n": "image/png",      # PNG
}


def _sniff_image_mime(content: bytes) -> Optional[str]:
    """根据文件头嗅探真实图片 MIME，非 jpg/png 返回 None。"""
    for magic, mime in _IMAGE_MAGIC.items():
        if content.startswith(magic):
            return mime
    return None


def _save_and_recognize(content: bytes, mime: str, db: Session, user_id: int) -> tuple:
    """在线程池中执行：同步落盘 + 同步大模型推理，避免阻塞事件循环。"""
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    ext = ".jpg" if mime == "image/jpeg" else ".png"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(upload_dir, saved_name), "wb") as f:
        f.write(content)
    result = ai_service.recognize_food(
        content, mime, cfg=_cfg(db, user_id, "vision", "glm-4v-flash")
    )
    return saved_name, result


@router.post("/recognize-food")
async def recognize_food(
    file: UploadFile = File(..., description="图片文件，仅 jpg/png，≤5MB"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """上传食物图片，识别食物并估算营养。"""
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        logger.warning(
            "recognize-food 拒绝：图片 %d 字节超限（user=%s, filename=%s）",
            len(content), user_id, file.filename,
        )
        raise AppException(400, "图片大小不能超过 5MB")

    # 校验真实文件类型（magic bytes），仅依赖扩展名可被改名绕过
    mime = _sniff_image_mime(content)
    if mime is None:
        logger.warning(
            "recognize-food 拒绝：非 jpg/png（user=%s, filename=%s, head=%r）",
            user_id, file.filename, content[:12],
        )
        raise AppException(
            400, "图片格式不支持，请上传 JPG / PNG 图片（HEIC / WebP 请先另存为 JPG）"
        )

    # 文件落盘 + 模型推理为同步阻塞操作，交给线程池执行，保护事件循环吞吐
    loop = asyncio.get_event_loop()
    saved_name, result = await loop.run_in_executor(
        None, _save_and_recognize, content, mime, db, user_id
    )

    foods = [FoodItem(**item) for item in result.get("food_list", [])]
    return resp(200, "success", RecognizeResponse(
        food_list=foods,
        total_calorie=float(result.get("total_calorie", 0)),
        image_url=f"/uploads/{saved_name}",
    ).model_dump())


@router.post("/generate-plan")
def generate_plan(
    body: Optional[PlanRequest] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """生成一日减脂食谱（落库 ai_diet_plan）。"""
    target_date = parse_date(body.date) if body and body.date else date.today()
    user = get_current_user(db, user_id)
    # 当日已摄入热量
    eaten = float(
        db.query(func.coalesce(func.sum(DietRecord.calorie), 0.0)).filter(
            DietRecord.user_id == user_id, DietRecord.record_date == target_date
        ).scalar() or 0
    )
    plan = ai_service.generate_plan(
        db, user, target_date, eaten,
        cfg=_cfg(db, user_id, "text", "glm-4-flash"),
    )
    return resp(200, "success", {"plan": PlanResponse(**plan).model_dump()})


@router.post("/chat")
def chat(
    body: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI 减脂营养师对话（多轮携带上下文 + 长期记忆）。"""
    user = get_current_user(db, user_id)
    reply = ai_service.chat(
        user, body.message, body.history or [], body.memories,
        cfg=_cfg(db, user_id, "text", "glm-4-flash"),
    )
    return resp(200, "success", ChatResponse(reply=reply).model_dump())


@router.post("/chat/stream")
def chat_stream(
    body: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI 对话流式输出（SSE）。

    事件类型：
    - `delta`：带 data 字段的文本片段
    - `done`：流结束
    - `error`：出错（message 为提示文案）
    """
    from fastapi.responses import StreamingResponse
    from utils.exceptions import AppException

    user = get_current_user(db, user_id)

    def gen():
        def sse(event: str, payload: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            for piece in ai_service.chat_stream(
                user, body.message, body.history or [], body.memories,
                cfg=_cfg(db, user_id, "text", "glm-4-flash"),
            ):
                yield sse("delta", {"data": piece})
            yield sse("done", {"data": ""})
        except AppException as e:
            yield sse("error", {"message": e.message})
        except Exception as e:  # noqa: BLE001
            yield sse("error", {"message": f"AI 服务异常：{e}"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/daily-review")
def daily_review(
    date: str = Query(None, description="YYYY-MM-DD，缺省为今天"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """生成当日饮食复盘（≤300 字）。"""
    d = parse_date(date) if date else today()
    review = ai_service.daily_review(
        db, user_id, d, cfg=_cfg(db, user_id, "text", "glm-4-flash")
    )
    return resp(200, "success", DailyReviewResponse(review=review).model_dump())


@router.get("/plan")
def get_plan(
    date: str = Query(None, description="YYYY-MM-DD，缺省为今天"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """读取已保存的当日食谱（不触发 AI 生成，用于首屏快速加载）。"""
    d = parse_date(date) if date else today()
    row = (
        db.query(AiDietPlan)
        .filter(AiDietPlan.user_id == user_id, AiDietPlan.plan_date == d)
        .order_by(AiDietPlan.id.desc())
        .first()
    )
    if not row:
        return resp(200, "success", {"plan": None})

    plan = {
        "breakfast": json.loads(row.breakfast or "[]"),
        "lunch": json.loads(row.lunch or "[]"),
        "dinner": json.loads(row.dinner or "[]"),
        "total_calorie": float(row.total_calorie or 0),
        "adapt_desc": row.adapt_desc or "",
    }
    return resp(200, "success", {"plan": PlanResponse(**plan).model_dump()})
