"""启动脚本"""
import os

import uvicorn

if __name__ == "__main__":
    reload_enabled = os.getenv("AIMAILER_RELOAD", "").lower() in {"1", "true", "yes"}
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        log_level="info",
    )
