"""轻享瘦 - AI 智能减脂管理系统 后端入口。

开发模式启动（前端走 vite dev server，双进程）：
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

生产/部署模式（后端单端口同时托管前端构建产物，单进程）：
    先在 frontend 执行 npm run build，再启动本服务；
    检测到 ../frontend/dist/index.html 后会自动托管 SPA，访问 http://<host>:8000 即可。

应用启动流程：
1. 加载 .env 环境变量。
2. 注册 CORS 中间件（最外层）。
3. 注册 JWT 鉴权中间件（内层，仅拦截 /api/**）。
4. 注册全局异常处理器。
5. 挂载所有 router（统一前缀 /api/v1）。
6. 挂载 /uploads 静态目录；若存在前端构建产物则一并托管 SPA。
7. 启动时校验密钥、创建上传目录、自动建表。
"""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
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


# 前端构建产物目录：存在 index.html 即视为「部署模式」，由后端统一托管。
# 开发模式下该目录不存在，前端仍由 vite dev server 提供。
_FRONTEND_DIST = os.getenv("FRONTEND_DIST") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)
_HAS_DIST = os.path.isfile(os.path.join(_FRONTEND_DIST, "index.html"))

# 上传目录：在导入期创建并挂载，确保顺序早于 SPA 的兜底路由
_UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(_UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.abspath(_UPLOAD_DIR)), name="uploads")


@app.get("/health")
def health():
    """健康检查（始终可用，供部署探活）。"""
    return resp(200, "ok", {"name": "轻享瘦"})


if _HAS_DIST:
    # ---- 部署模式：托管前端 SPA（history 路由回退到 index.html） ----
    _ASSETS_DIR = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.isdir(_ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")

    @app.get("/", include_in_schema=False)
    async def spa_index():
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """真实存在的静态文件直接返回，其余交给前端路由。"""
        candidate = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))

else:
    # ---- 开发模式：根路径返回服务信息，前端由 5173 提供 ----
    @app.get("/")
    def index():
        return resp(200, "ok", {"name": "轻享瘦", "docs": "/docs"})


@app.on_event("startup")
def on_startup():
    """启动时：校验密钥强度 + 确保上传目录存在 + 自动建表。"""
    validate_jwt_secret()
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    create_tables()


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
