"""FastAPI 主应用入口"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine
from app.init_db import init_database
from app.routers import (
    auth, dashboard, mail_account, recipients, models,
    sources, jobs, storage, email_template, schedule,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    init_database()
    # 启动调度器
    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[warn] Scheduler startup failed: {e}")
    yield
    # 关闭时
    try:
        from app.services.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
for router_module in [auth, dashboard, mail_account, recipients, models, sources, jobs, storage, email_template, schedule]:
    app.include_router(router_module.router)


# 健康检查
@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# 前端静态文件服务
frontend_dist = Path(__file__).parent / "static"
if frontend_dist.exists():
    # 挂载静态资源
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA路由：所有非API路径返回index.html"""
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))
else:
    @app.get("/")
    async def root():
        return HTMLResponse("""
        <html><body style="font-family:sans-serif;padding:40px;">
        <h1>🤖 AI Tech Digest Mailer</h1>
        <p>后端服务已启动。</p>
        <p>请先构建前端：<code>cd frontend && npm run build</code>，然后将 dist 目录内容复制到 <code>backend/app/static/</code></p>
        <p>或者启动前端开发服务器：<code>cd frontend && npm run dev</code></p>
        <p>API文档：<a href="/api/docs">/api/docs</a></p>
        </body></html>
        """)
