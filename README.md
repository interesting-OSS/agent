# 墨庐 (MoLu) — AI 小说写作系统

> 文人书房，墨香氤氲。多智能体协作的 AI 小说写作平台。

## 系统架构

```
frontend (Next.js 16)          backend (FastAPI)
    :3000  ──rewrites──▶  :8000
       │                      ├─ Agents (Writer/Supervisor/Inspector/Guardian/Custodian/Architect)
       │                      ├─ LLM (DeepSeek/Kimi/Qwen)
       │                      └─ SQLite
```

### 多智能体协作

| 智能体 | 职责 | 默认模型 |
|--------|------|----------|
| **Writer** | 主笔创作章节 | DeepSeek |
| **Supervisor** | 统筹全局、分配任务 | DeepSeek |
| **Architect** | 规划大纲、世界观 | DeepSeek |
| **Inspector** | 审校内容质量 | Kimi |
| **Guardian** | 安全检查、规则守护 | Qwen |
| **Custodian** | 记忆管理、上下文维护 | Qwen |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 20.9+
- npm 或 pnpm

### 1. 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 复制并编辑环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key（至少配置 DeepSeek）

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:3000`。

### 3. 创建你的第一部小说

1. 首页点击「创建第一部作品」
2. 输入书名，选择类型（仙侠/科幻/都市/奇幻）
3. 进入 setup 页面：选择类型 → 设定世界观 → 设定角色
4. 进入写作页面，AI 开始逐章创作

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── agents/         # 多智能体（Writer/Supervisor/Inspector/Guardian/…）
│   │   ├── api/v1/         # REST API 路由
│   │   ├── genre/          # 小说类型配置（仙侠/科幻/都市/奇幻）
│   │   ├── llm/            # LLM 提供商适配（DeepSeek/Kimi/Qwen）
│   │   ├── middleware/     # 认证中间件
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── services/       # 业务逻辑（自动角色/导出/伏笔/记忆/…）
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置管理
│   │   └── database.py     # 数据库连接（SQLite）
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router 页面
│   │   │   ├── dashboard/  # 书房首页
│   │   │   ├── novels/[id]/setup/   # 小说初始化向导
│   │   │   └── novels/[id]/write/   # AI 写作界面
│   │   ├── components/     # React 组件
│   │   ├── lib/api.ts      # API 客户端
│   │   └── stores/         # Zustand 状态管理
│   ├── next.config.ts
│   └── package.json
└── .gitignore
```

## 技术栈

| 层 | 技术 |
|----|------|
| 前端框架 | Next.js 16 + React 19 |
| UI 组件 | Ant Design 6 + Tailwind CSS 4 |
| 状态管理 | Zustand |
| 后端框架 | FastAPI (Python) |
| 数据库 | SQLite + SQLAlchemy (async) |
| 迁移工具 | Alembic |
| LLM | DeepSeek / Kimi / Qwen (OpenAI 兼容 API) |
| 编辑器 | TipTap (富文本) |

## License

MIT
