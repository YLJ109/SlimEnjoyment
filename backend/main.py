"""轻享瘦 - AI 智能减脂管理系统 后端入口。

启动方式：
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

应用启动流程：
1. 加载 .env 环境变量。
2. 注册 CORS 中间件（最外层）。
3. 注册 JWT 鉴权中间件（内层）。
4. 注册全局异常处理器。
5. 挂载所有 router（统一前缀 /api/v1）。
6. 启动时自动创建 uploads 目录并建表（Base.metadata.create_all）。
"""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from database.db import create_tables
from middleware.cors import add_cors
from middleware.auth import AuthMiddleware
from utils.exceptions import register_exception_handlers
from utils.common import resp
from utils.security import validate_jwt_secret

from routers import auth, user, diet, weight, ai, exercise, water, stats

# 加载环境变量（若存在 .env）
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="轻享瘦 - AI 智能减脂管理系统",
    description="基于 FastAPI + 智谱 AI 的智能减脂管理后端",
    version="1.0.0",
)

# 1. CORS 中间件（最外层，处理跨域与预检）
add_cors(app)

# 2. JWT 鉴权中间件（内层，解析 token 注入 request.state.user_id）
app.add_middleware(AuthMiddleware)

# 3. 全局异常处理
register_exception_handlers(app)

# 4. 挂载路由
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(diet.router)
app.include_router(weight.router)
app.include_router(ai.router)
app.include_router(exercise.router)
app.include_router(water.router)
app.include_router(stats.router)


@app.on_event("startup")
def on_startup():
    """启动时：校验密钥强度 + 创建上传目录 + 自动建表 + 挂载静态资源。"""
    validate_jwt_secret()

    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    create_tables()

    # 挂载上传目录，使 /uploads/<file> 可公开访问（图片识别结果回显用）
    abs_upload = os.path.abspath(upload_dir)
    if not any(
        getattr(m, "path", "") == abs_upload for m in app.routes
    ):
        app.mount("/uploads", StaticFiles(directory=abs_upload), name="uploads")


@app.get("/")
@app.get("/health")
def health():
    """健康检查。"""
    return resp(200, "ok", {"name": "轻享瘦"})


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
