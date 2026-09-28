"""AI 相关 Pydantic 模型。"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any


class FoodItem(BaseModel):
    """识别出的单个食物营养信息。"""
    model_config = ConfigDict(extra="ignore")

    name: str
    weight: float
    calorie: float
    protein: float
    fat: float
    carbohydrate: float
    sugar: float
    fiber: float
    sodium: float


class RecognizeResponse(BaseModel):
    """图片识别返回。"""
    food_list: List[FoodItem]
    total_calorie: float
    image_url: Optional[str] = None


class PlanFood(BaseModel):
    """食谱中的单个菜品。"""
    model_config = ConfigDict(extra="ignore")

    name: str
    weight: str
    calorie: float
    practice: str


class PlanResponse(BaseModel):
    """一日食谱返回。"""
    breakfast: List[PlanFood]
    lunch: List[PlanFood]
    dinner: List[PlanFood]
    total_calorie: float
    adapt_desc: str


class PlanRequest(BaseModel):
    """生成食谱请求（date 可选，默认今天）。"""
    date: Optional[str] = None


class ChatRequest(BaseModel):
    """AI 对话请求。"""
    message: str
    history: Optional[List[Any]] = None
    # 用户长期记忆（前端维护，随请求注入 system prompt）
    memories: Optional[List[str]] = None


class ChatResponse(BaseModel):
    """AI 对话返回。"""
    reply: str


class DailyReviewResponse(BaseModel):
    """每日复盘返回。"""
    review: str
