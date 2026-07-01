# AI Tech Digest Mailer

> 一个自托管的 AI 技术前沿日报生成器，自动追踪 RSS、GitHub Trending 等信源，调用兼容 OpenAI / Anthropic 的 LLM 接口生成中文技术简报，并通过 QQ 邮箱定时发送给用户。

## 功能概览

- **信息采集**：支持 RSS 信源、GitHub Trending 抓取
- **LLM 日报生成**：兼容 OpenAI Chat Completions / Responses / Anthropic Messages 三种接口
- **HTML 邮件发送**：通过 QQ 邮箱 SMTP 发送美观的 HTML 日报
- **定时任务调度**：每日自动采集、生成日报、发送邮件
- **Admin 管理后台**：完整的配置管理界面
- **存储与日志**：采集记录、日报内容、邮件日志、LLM调用日志

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy / APScheduler |
| 前端 | React 18 / TypeScript / Vite / Tailwind CSS |
| 数据库 | SQLite（MVP）/ PostgreSQL（可扩展） |
| 部署 | Docker / Docker Compose |

## 快速开始

### 方式一：直接运行

**1. 安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

**2. 初始化数据库**
```bash
python -c "from app.init_db import init_database; init_database()"
```

**3. 构建前端**
```bash
cd frontend
npm install
npm run build
```

**4. 部署前端到后端**
```bash
# Windows
Copy-Item -Path frontend\dist\* -Destination backend\app\static\ -Recurse -Force

# Linux/Mac
cp -r frontend/dist/* backend/app/static/
```

**5. 启动服务**
```bash
cd backend
python run.py
```

访问 http://localhost:8000 即可打开管理后台。

### 方式二：Docker 部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

## 默认账户

| 项目 | 值 |
|---|---|
| 用户名 | admin |
| 密码 | admin123 |

> 首次登录后会提示修改密码。

## 配置说明

### 环境变量（backend/.env）

```env
# JWT密钥（请修改为随机字符串）
SECRET_KEY=your-secret-key

# 敏感数据加密密钥
ENCRYPTION_KEY=your-encryption-key

# 默认管理员
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
```

### 使用流程

1. 登录 Admin 后台
2. 配置 QQ 邮箱 SMTP 授权码
3. 添加收件人邮箱
4. 配置 LLM 模型（OpenAI / Anthropic 兼容接口）
5. 添加 RSS / GitHub Trending 信源
6. 点击"立即采集"测试
7. 点击"生成日报"测试
8. 启用每日定时任务

## API 文档

启动服务后访问 http://localhost:8000/api/docs 查看 Swagger API 文档。

## 项目结构

```
aimailer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py             # 配置
│   │   ├── database.py           # 数据库连接
│   │   ├── security.py           # 加密 / JWT / 密码哈希
│   │   ├── init_db.py            # 数据库初始化
│   │   ├── models/               # SQLAlchemy 模型
│   │   ├── schemas/              # Pydantic 数据模型
│   │   ├── routers/              # API 路由
│   │   │   ├── auth.py           # 认证
│   │   │   ├── dashboard.py      # 仪表盘
│   │   │   ├── mail_account.py    # 邮箱配置
│   │   │   ├── recipients.py      # 收件人
│   │   │   ├── models.py          # 模型配置
│   │   │   ├── sources.py         # 信源配置
│   │   │   ├── jobs.py            # 任务管理
│   │   │   ├── storage.py         # 存储管理
│   │   │   ├── email_template.py  # 邮件模板
│   │   │   └── schedule.py        # 调度配置
│   │   ├── services/             # 业务服务
│   │   │   ├── auth_service.py    # 认证依赖
│   │   │   ├── llm_client.py      # LLM 适配器
│   │   │   ├── fetcher.py         # 信息采集器
│   │   │   ├── mail_service.py    # 邮件发送
│   │   │   ├── email_renderer.py  # HTML 渲染
│   │   │   ├── digest_service.py  # 日报生成
│   │   │   └── scheduler.py       # 任务调度
│   │   └── static/                # 前端构建产物
│   ├── data/                     # SQLite 数据库
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── pages/                # 页面组件
│   │   ├── components/           # 通用组件
│   │   ├── api/                  # API 客户端
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 支持的信源类型

| 类型 | 说明 |
|---|---|
| rss | RSS/Atom 订阅源 |
| github_trending | GitHub Trending 项目 |
| hackernews_rss | Hacker News RSS |
| arxiv_rss | Arxiv 论文 RSS |

## 支持的 LLM 接口

| 接口类型 | 说明 |
|---|---|
| openai_completion | OpenAI Chat Completions (/v1/chat/completions) |
| openai_responses | OpenAI Responses API (/v1/responses) |
| anthropic_messages | Anthropic Messages API (/v1/messages) |

## 安全特性

- SMTP 授权码和 API Key 使用 Fernet 对称加密存储
- 密码使用 bcrypt 哈希
- JWT Token 认证
- 前端不回显完整密钥（掩码显示）
- 日志不记录敏感信息
