"""AI 相关 Pydantic 模型。"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any


class FoodItem(BaseModel):
    """识别出的单个食物营养信息。

    数值字段均给默认值：模型偶发漏字段时降级为 0，而非直接 500。
    """
    model_config = ConfigDict(extra="ignore")

    name: str
    # 数量（个 / 份）。同一张图里可能有多个相同食物，用它区分，默认 1。
    quantity: float = 1
    weight: float = 0
    calorie: float = 0
    protein: float = 0
    fat: float = 0
    carbohydrate: float = 0
    sugar: float = 0
    fiber: float = 0
    sodium: float = 0


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
