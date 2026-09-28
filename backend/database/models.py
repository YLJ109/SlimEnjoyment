"""全部 7 张表的 ORM 模型定义。

表清单：
1. user            用户信息 + 代谢指标
2. diet_record     饮食记录
3. weight_record   体重记录（按天唯一，计算差值）
4. ai_diet_plan    AI 生成的一日减脂食谱
5. exercise_record 运动记录
6. water_record    饮水记录（按天唯一，累加）
7. user_checkin    用户打卡（连续天数）
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, UniqueConstraint,
)
from datetime import datetime

from database.db import Base


class User(Base):
    """用户表：保存基础体征信息与计算得到的代谢指标。"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # 性别：0 女 / 1 男
    gender = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    height = Column(Float, nullable=False)
    current_weight = Column(Float, nullable=False)
    target_weight = Column(Float, nullable=False)
    # 活动水平：1 久坐1.2 / 2 轻度1.375 / 3 中度1.55 / 4 重度1.725
    activity_level = Column(Integer, nullable=False)
    # 基础代谢率（BMR）
    bmr = Column(Float, nullable=False)
    # 每日总消耗（TDEE）
    tdee = Column(Float, nullable=False)
    # 推荐每日摄入热量（TDEE - 400，不低于 BMR）
    recommend_calorie = Column(Float, nullable=False)
    # 饮食偏好（JSON 字符串，可空）
    diet_preference = Column(Text, nullable=True)
    # 忌口 / 过敏（纯文本，可空）
    diet_avoid = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DietRecord(Base):
    """饮食记录表：每餐一条记录。"""
    __tablename__ = "diet_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    # 记录日期
    record_date = Column(Date, index=True, nullable=False)
    # 餐型：1 早 / 2 午 / 3 晚 / 4 加餐
    meal_type = Column(Integer, nullable=False)
    # 食物描述
    food_desc = Column(Text, nullable=False)
    # 食物图片路径（可空）
    food_image_path = Column(String(255), nullable=True)
    # 录入方式：1 文字 / 2 图片
    input_type = Column(Integer, nullable=False)
    calorie = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    carbohydrate = Column(Float, nullable=False)
    sugar = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)
    sodium = Column(Float, nullable=False)
    create_time = Column(DateTime, default=datetime.now)


class WeightRecord(Base):
    """体重记录表：同一天只保留最新，新增时计算与上一记录的差值。"""
    __tablename__ = "weight_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    # 记录日期（与 user_id 联合唯一）
    record_date = Column(Date, index=True, nullable=False)
    weight = Column(Float, nullable=False)
    # 体脂率（可空）
    body_fat = Column(Float, nullable=True)
    # 腰围（可空）
    waist = Column(Float, nullable=True)
    # 与上一条记录的差值
    weight_diff = Column(Float, nullable=False)
    remark = Column(String(255), nullable=True)
    create_time = Column(DateTime, default=datetime.now)

    # 联合唯一约束（用户 + 日期）：同一天只保留一条最新记录
    __table_args__ = (
        UniqueConstraint("user_id", "record_date", name="uq_weight_user_date"),
    )


class AiDietPlan(Base):
    """AI 生成的一日减脂食谱表。"""
    __tablename__ = "ai_diet_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    plan_date = Column(Date, index=True, nullable=False)
    # 早餐（JSON 字符串）
    breakfast = Column(Text, nullable=False)
    lunch = Column(Text, nullable=False)
    dinner = Column(Text, nullable=False)
    total_calorie = Column(Float, nullable=False)
    # 方案说明（可空）
    adapt_desc = Column(String(255), nullable=True)
    create_time = Column(DateTime, default=datetime.now)


class ExerciseRecord(Base):
    """运动记录表。"""
    __tablename__ = "exercise_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    record_date = Column(Date, index=True, nullable=False)
    exercise_type = Column(String(50), nullable=False)
    # 时长（分钟）
    duration = Column(Integer, nullable=False)
    # 消耗热量
    calorie_burn = Column(Float, nullable=False)
    create_time = Column(DateTime, default=datetime.now)


class WaterRecord(Base):
    """饮水记录表：同一天累加，目标量 = 体重 * 35ml。"""
    __tablename__ = "water_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    # 记录日期（与 user_id 联合唯一）
    record_date = Column(Date, index=True, nullable=False)
    # 当日累计饮水量（ml）
    total_amount = Column(Integer, nullable=False)
    # 目标饮水量（ml）
    target_amount = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.now)

    # 联合唯一约束（用户 + 日期）：同一天累加同一条记录
    __table_args__ = (
        UniqueConstraint("user_id", "record_date", name="uq_water_user_date"),
    )


class UserCheckin(Base):
    """用户打卡表：记录连续打卡天数。"""
    __tablename__ = "user_checkin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    checkin_date = Column(Date, nullable=False)
    # 连续打卡天数
    continuous_days = Column(Integer, nullable=False)
    # 状态：1 正常
    status = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.now)

    # 联合唯一约束（用户 + 日期）
    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date", name="uq_checkin_user_date"),
    )


class UserAISettings(Base):
    """用户大模型配置：文字 / 视觉理解 / 语言转文字 三套独立配置。

    每套能力各自选国内厂商（provider）+ 填 Key + 填模型名（model）；
    custom 厂商额外填 base_url。三套可混搭不同厂商。
    该表是关键个性化配置，由「我的」页维护，并同步写 .env。
    """
    __tablename__ = "user_ai_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 与 user 一对一
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, index=True, nullable=False)

    # 文字（对话 / 食谱 / 复盘）
    text_provider = Column(String(30), nullable=True)
    text_api_key = Column(Text, nullable=True)
    text_model = Column(String(80), nullable=True)
    text_base_url = Column(Text, nullable=True)

    # 视觉理解（食物图片识别等）
    vision_provider = Column(String(30), nullable=True)
    vision_api_key = Column(Text, nullable=True)
    vision_model = Column(String(80), nullable=True)
    vision_base_url = Column(Text, nullable=True)

    # 语言转文字（ASR）——当前识别引擎为浏览器内置 Web Speech API，
    # 这里的配置作为服务端 ASR 的预留，后续可按厂商接入。
    asr_provider = Column(String(30), nullable=True)
    asr_api_key = Column(Text, nullable=True)
    asr_model = Column(String(80), nullable=True)
    asr_base_url = Column(Text, nullable=True)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
