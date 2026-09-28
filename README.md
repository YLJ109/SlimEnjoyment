# 轻享瘦 · AI 智能减脂管理系统

面向普通减脂人群的轻量级 Web 应用：**拍照/文字双模态智能记录饮食 + 个性化食谱推荐 + 数据可视化复盘**。纯本地即可运行，手机浏览器打开即用。

- 前端：Vue 3 + Vite 5 + Pinia + Vue Router 4 + Vant 4 + ECharts 5 + Axios + Less + REM 响应式（移动端优先，适配 320–768px）
- 后端：FastAPI + Uvicorn + SQLAlchemy 2.0 + SQLite 3 + Pydantic v2 + PyJWT + passlib(bcrypt) + 智谱 AI（zhipuai）
- AI 模型：图片识别 `glm-4v-flash`、文本/食谱/对话/复盘 `glm-4-flash`（均免费）

---

## 目录结构

```
JianFeiWeb/
├── backend/                 # 后端工程
│   ├── main.py              # 入口，启动时自动建表
│   ├── .env.example         # 环境变量模板
│   ├── requirements.txt
│   ├── database/            # db.py（连接/会话）、models.py（8 张表，含 user_ai_settings）
│   ├── routers/             # auth/user/diet/weight/ai/exercise/water/stats
│   ├── services/            # auth/user/ai/diet/stats/calc 业务逻辑
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── middleware/          # JWT 鉴权、CORS
│   ├── utils/               # 安全、通用、异常
│   └── uploads/             # 图片存储（自动创建）
└── frontend/                # 前端工程
    ├── index.html / package.json / vite.config.js / .env.development
    └── src/
        ├── main.js / App.vue / router / store(Pinia)
        ├── api/             # request 封装 + 各模块接口
        ├── views/           # 9 个页面
        ├── components/      # NavBar/CalorieCard/DietItem/ChartLine/ChartPie/StatsPanel（+ layout/ icons/）
        ├── utils/ / styles/ # 工具与 Less 设计系统「运动能量·暗夜工业」（主色 lime #c6f24e）
```

---

## 快速开始

> 已验证：后端依赖安装、服务启动、注册/登录/指标/饮食接口全部通过；前端 `npm run build` 构建通过。

### 1. 后端

```bash
cd backend
python -m venv .venv            # 或 python3 -m venv .venv
.venv\Scripts\activate           # Windows；Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt # 国内镜像可加 -i https://pypi.tuna.tsinghua.edu.cn/simple
cp .env.example .env            # 如需启用 AI，编辑 .env 填入 ZHIPU_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- 启动后访问 `http://localhost:8000/docs` 查看 Swagger 文档。
- **数据库 `diet.db` 在首次启动时由 SQLAlchemy 自动创建**，无需手动建表。
- 未配置任何 AI Key 时，注册/登录/记录/统计等核心功能完全正常。AI 相关接口会返回**友好业务提示**（HTTP 400），不会 500：例如对话返回「未配置「文字」模型的 Key，请到「我的」页配置（国内大模型均可）」；食谱生成自动**降级为本地通用方案**（仍返回 200，可直接使用）。
- 支持**运行时配置**：登录后在「我的 → 大模型配置」填入文字/视觉/语音三套 Key（国内大模型均可，厂商可混搭），保存后写库并同步 `.env`，无需手改文件；语音识别走浏览器内置 Web Speech API，无需 Key。

### 2. 前端

```bash
cd frontend
npm install                    # 已配置 npmmirror 镜像
npm run dev                    # 开发服务器 http://localhost:5173
```

- 开发期通过 Vite 代理把 `/api` 转发到 `http://localhost:8000`，因此无需处理跨域。
- 生产构建：`npm run build`（产物在 `dist/`），可用任意静态服务器托管。
- 手机访问：手机与电脑同一局域网，浏览器打开 `http://<电脑IP>:5173` 即可。

---

## 配置智谱 AI（可选但推荐）

1. 注册并获取智谱开放平台 API Key：https://open.bigmodel.cn
2. 编辑 `backend/.env`，设置：
   ```
   ZHIPU_API_KEY=你的key
   ```
3. 重启后端。之后「拍照识别食物 / 生成食谱 / AI 对话 / 每日复盘」即可使用。

> **默认全部使用智谱【永久免费】的 Flash 系列模型**，开箱即用不产生费用：
> 文字 `glm-4-flash`、视觉 `glm-4v-flash`、语音 `glm-4-flash`。
> 在「我的 → 大模型配置」中，模型名下方会列出该厂商的免费模型清单并打「免费」徽标；
> 如需更强效果再手动改成付费模型即可。

`.env` 其它可配项：`JWT_SECRET`（缺省或仍为占位值时会**自动生成随机密钥并打印告警**，生产可直接使用或显式指定长随机串）、`JWT_EXPIRE_DAYS=7`、`DB_PATH=diet.db`、`UPLOAD_DIR=uploads`、`HOST`、`PORT`。

---

## 功能清单

- 账号：注册 / 登录 / JWT 鉴权（7 天）/ 首次信息采集（BMI·推荐热量·预计达成时间实时预览）
- 饮食：文字 / 拍照双模态记录，按早午晚加餐分组，左滑删除、编辑，AI 识别结果需确认后保存（拍照原图会**在前端自动压缩并转 JPG** 再上传，兼容手机大图与 HEIC/WebP）
- 体重：记录 / 趋势，同日覆盖并计算差值
- 运动：类型 + 时长，按 MET 自动估算消耗
- 饮水：每日目标 = 体重 × 35ml，一键 +200/500ml
- AI：图片识食物、生成一日减脂食谱（落库）、多轮营养对话、每日 ≤300 字复盘
- 统计：体重趋势（日/周/月，标注目标线）、营养分析（柱状 + 供能比饼图）、周度报告
- 体验：暗夜工业深色主题（lime 主色 `#c6f24e`）、卡片化、深色/浅色切换、移动端优先适配、下拉刷新、Toast/Notify 提示

## 接口一览（前缀 `/api/v1`）

| 模块 | 方法 | 路径 |
| --- | --- | --- |
| 认证 | POST | /auth/register · /auth/login · GET /auth/info |
| 用户 | PUT | /user/profile · /user/preference · GET /user/metrics |
| 饮食 | POST/GET/PUT/DELETE | /diet/add · /diet/list · /diet/{id} · /diet/today |
| 体重 | POST/GET/DELETE | /weight/add · /weight/list · /weight/{id} |
| 运动 | POST/GET/DELETE | /exercise/add · /exercise/list · /exercise/{id} |
| 饮水 | POST/GET | /water/add · /water/today |
| AI | POST/GET | /ai/recognize-food · /ai/generate-plan · /ai/chat · /ai/daily-review |
| 统计 | GET | /stats/daily · /stats/weekly · /stats/weight-trend · /stats/nutrient-trend |

统一响应：`{"code":200,"message":"success","data":{}}`；错误码 200/400/401/403/500。

---

## 备注

- 所有日期默认取服务端日期，避免客户端时间误差。
- 安全：密码 bcrypt 哈希、JWT 鉴权中间件（`OPTIONS` 预检放行）、CORS 白名单（`CORS_ORIGINS` 可配）、**大模型 Key 落库静态加密**（由 `JWT_SECRET` 派生 Fernet，读取时解密，脱敏仅回显末 4 位）、文件上传 magic-bytes 真实类型校验 + 大小限制（jpg/png、≤5MB、UUID 重命名）。
- 业务规则：每日热量缺口 300–500 kcal；体重同日仅留最新；连续打卡按昨日状态递增/重置；AI 结果需用户确认。
