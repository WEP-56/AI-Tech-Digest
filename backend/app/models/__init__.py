"""所有数据库模型定义"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    """返回 naive UTC datetime（SQLite 不存储时区信息，统一用 naive）"""
    return datetime.utcnow()


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)
    must_change_password = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class MailAccount(Base):
    __tablename__ = "mail_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), nullable=False)
    sender_name = Column(String(100), nullable=False)
    smtp_host = Column(String(200), default="smtp.qq.com", nullable=False)
    smtp_port = Column(Integer, default=465, nullable=False)
    smtp_security = Column(String(20), default="ssl", nullable=False)
    smtp_auth_code_encrypted = Column(Text, nullable=False)
    imap_host = Column(String(200), default="imap.qq.com", nullable=False)
    imap_port = Column(Integer, default=993, nullable=False)
    imap_security = Column(String(20), default="ssl", nullable=False)
    imap_auth_code_encrypted = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    recipients = relationship("Recipient", back_populates="mail_account")


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    recipient_type = Column(String(10), default="to", nullable=False)  # to / cc / bcc
    topics = Column(Text, nullable=True)  # 逗号分隔的主题
    frequency = Column(String(20), default="daily", nullable=False)  # daily / weekly / manual
    enabled = Column(Boolean, default=True, nullable=False)
    remark = Column(Text, nullable=True)
    mail_account_id = Column(Integer, ForeignKey("mail_accounts.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    mail_account = relationship("MailAccount", back_populates="recipients")
    email_logs = relationship("EmailLog", back_populates="recipient")


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)  # openai_completion / openai_responses / anthropic_messages
    base_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    model_name = Column(String(200), nullable=False)
    temperature = Column(Float, default=0.3, nullable=False)
    max_output_tokens = Column(Integer, default=4000, nullable=False)
    timeout_seconds = Column(Integer, default=60, nullable=False)
    retry_count = Column(Integer, default=2, nullable=False)
    anthropic_version = Column(String(20), default="2023-06-01", nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    llm_call_logs = relationship("LLMCallLog", back_populates="model_config")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=False)  # rss / github_trending / web_page / hackernews_rss / arxiv_rss / custom_api
    url = Column(String(1000), nullable=False)
    category = Column(String(100), nullable=True)
    language = Column(String(20), default="zh", nullable=False)
    include_keywords = Column(Text, nullable=True)  # 逗号分隔
    exclude_keywords = Column(Text, nullable=True)
    fetch_interval = Column(String(20), default="daily", nullable=False)
    max_items = Column(Integer, default=30, nullable=False)
    need_full_text = Column(Boolean, default=False, nullable=False)
    send_to_llm = Column(Boolean, default=True, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    # GitHub Trending 专用
    github_language = Column(String(50), nullable=True)
    github_since = Column(String(20), default="daily", nullable=True)
    min_stars = Column(Integer, default=0, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    raw_items = relationship("RawItem", back_populates="source", cascade="all, delete-orphan")
    fetch_logs = relationship("SourceFetchLog", back_populates="source", cascade="all, delete-orphan")


class RawItem(Base):
    __tablename__ = "raw_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    author = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=utcnow, nullable=False)
    url_hash = Column(String(64), index=True, nullable=True)
    title_hash = Column(String(64), index=True, nullable=True)
    content_hash = Column(String(64), nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending / processed / skipped
    # 额外字段（GitHub Trending用）
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    source = relationship("Source", back_populates="raw_items")


class ProcessedItem(Base):
    __tablename__ = "processed_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_item_id = Column(Integer, ForeignKey("raw_items.id"), nullable=True)
    digest_job_id = Column(Integer, ForeignKey("digest_jobs.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # JSON数组
    importance = Column(Integer, default=1, nullable=False)
    source_name = Column(String(200), nullable=True)
    source_url = Column(String(1000), nullable=True)
    llm_model = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class DigestJob(Base):
    __tablename__ = "digest_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    job_type = Column(String(50), default="daily", nullable=False)  # daily / manual
    status = Column(String(30), default="pending", nullable=False)  # pending / running / success / failed / partial_success
    raw_count = Column(Integer, default=0, nullable=False)
    filtered_count = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    email_sent_count = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    outputs = relationship("DigestOutput", back_populates="job", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="digest_job")
    llm_call_logs = relationship("LLMCallLog", back_populates="digest_job")


class DigestOutput(Base):
    __tablename__ = "digest_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_job_id = Column(Integer, ForeignKey("digest_jobs.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    json_content = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    job = relationship("DigestJob", back_populates="outputs")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_job_id = Column(Integer, ForeignKey("digest_jobs.id"), nullable=True, index=True)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=True)
    recipient_email = Column(String(200), nullable=False)
    subject = Column(String(500), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending / sent / failed
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    digest_job = relationship("DigestJob", back_populates="email_logs")
    recipient = relationship("Recipient", back_populates="email_logs")


class SourceFetchLog(Base):
    __tablename__ = "source_fetch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False)  # success / failed / partial
    fetched_count = Column(Integer, default=0, nullable=False)
    new_count = Column(Integer, default=0, nullable=False)
    http_status_code = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    source = relationship("Source", back_populates="fetch_logs")


class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_job_id = Column(Integer, ForeignKey("digest_jobs.id"), nullable=True, index=True)
    model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=True)
    provider_type = Column(String(50), nullable=True)
    model_name = Column(String(200), nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # success / failed
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    digest_job = relationship("DigestJob", back_populates="llm_call_logs")
    model_config = relationship("ModelConfig", back_populates="llm_call_logs")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), default="default", nullable=False)
    subject_template = Column(String(500), default="{{date}} AI 前沿日报", nullable=False)
    html_template = Column(Text, nullable=True)  # Jinja2模板，留空使用内置默认
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ScheduleConfig(Base):
    __tablename__ = "schedule_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enabled = Column(Boolean, default=False, nullable=False)
    timezone = Column(String(50), default="Asia/Shanghai", nullable=False)
    fetch_time = Column(String(10), default="07:00", nullable=False)
    digest_time = Column(String(10), default="07:20", nullable=False)
    send_time = Column(String(10), default="07:30", nullable=False)
    weekdays_only = Column(Boolean, default=False, nullable=False)
    retry_count = Column(Integer, default=2, nullable=False)
    retry_interval_minutes = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
