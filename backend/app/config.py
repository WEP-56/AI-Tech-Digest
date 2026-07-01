"""应用配置"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "AI Tech Digest Mailer"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "change-this-secret-key-in-production-please-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{Path(__file__).parent.parent / 'data' / 'digest.db'}"

    # 加密密钥（用于加密授权码/API Key）
    ENCRYPTION_KEY: str = "change-this-encryption-key-32-bytes!!"  # 32字节

    # 默认管理员
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # 前端静态文件目录
    STATIC_DIR: str = str(Path(__file__).parent / "static")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保数据目录存在
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(parents=True, exist_ok=True)
