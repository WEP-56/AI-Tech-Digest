"""Pydantic 数据模型（请求/响应Schema）"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

# 关闭 model_ 保护命名空间（避免 model_name 字段冲突警告）
class _BaseSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


# ==================== 通用 ====================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class TokenData(BaseModel):
    username: Optional[str] = None


class StandardResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    success: bool = True
    total: int = 0
    page: int = 1
    page_size: int = 20
    data: list[Any] = []


# ==================== Auth ====================
class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class AdminUserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    must_change_password: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Dashboard ====================
class DashboardSummary(BaseModel):
    today_raw_count: int = 0
    today_valid_count: int = 0
    today_processed_count: int = 0
    today_email_sent: int = 0
    today_email_failed: int = 0
    last_job_time: Optional[datetime] = None
    last_error: Optional[str] = None
    enabled_sources: int = 0
    enabled_recipients: int = 0
    default_model_status: Optional[str] = None
    smtp_status: str = "未配置"


# ==================== Mail Account ====================
class MailAccountBase(BaseModel):
    email: str
    sender_name: str = ""
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_security: str = "ssl"
    imap_host: str = "imap.qq.com"
    imap_port: int = 993
    imap_security: str = "ssl"
    enabled: bool = True


class MailAccountCreate(MailAccountBase):
    smtp_auth_code: str
    imap_auth_code: Optional[str] = None


class MailAccountUpdate(BaseModel):
    email: Optional[str] = None
    sender_name: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_security: Optional[str] = None
    smtp_auth_code: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_security: Optional[str] = None
    imap_auth_code: Optional[str] = None
    enabled: Optional[bool] = None


class MailAccountResponse(MailAccountBase):
    id: int
    smtp_auth_code_masked: str = ""
    imap_auth_code_masked: str = ""
    has_smtp_auth_code: bool = False
    has_imap_auth_code: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Recipient ====================
class RecipientBase(BaseModel):
    name: str
    email: str
    recipient_type: str = "to"
    topics: Optional[str] = None
    frequency: str = "daily"
    enabled: bool = True
    remark: Optional[str] = None


class RecipientCreate(RecipientBase):
    pass


class RecipientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    recipient_type: Optional[str] = None
    topics: Optional[str] = None
    frequency: Optional[str] = None
    enabled: Optional[bool] = None
    remark: Optional[str] = None


class RecipientResponse(RecipientBase):
    id: int
    mail_account_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Model Config ====================
class ModelConfigBase(_BaseSchema):
    name: str
    provider_type: str
    base_url: str
    model_name: str
    temperature: float = 0.3
    max_output_tokens: int = 4000
    timeout_seconds: int = 60
    retry_count: int = 2
    anthropic_version: str = "2023-06-01"
    enabled: bool = True
    is_default: bool = False


class ModelConfigCreate(ModelConfigBase):
    api_key: str


class ModelConfigUpdate(_BaseSchema):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None
    retry_count: Optional[int] = None
    anthropic_version: Optional[str] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    id: int
    api_key_masked: str = ""
    has_api_key: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelTestRequest(BaseModel):
    pass


class ModelTestResult(BaseModel):
    success: bool
    message: str
    response_text: Optional[str] = None
    latency_ms: Optional[int] = None


# ==================== Source ====================
class SourceBase(BaseModel):
    name: str
    source_type: str
    url: str
    category: Optional[str] = None
    language: str = "zh"
    include_keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None
    max_items: int = 30
    need_full_text: bool = False
    send_to_llm: bool = True
    weight: float = 1.0
    enabled: bool = True
    github_language: Optional[str] = None
    github_since: str = "daily"
    min_stars: int = 0


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    include_keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None
    max_items: Optional[int] = None
    need_full_text: Optional[bool] = None
    send_to_llm: Optional[bool] = None
    weight: Optional[float] = None
    enabled: Optional[bool] = None
    github_language: Optional[str] = None
    github_since: Optional[str] = None
    min_stars: Optional[int] = None


class SourceResponse(SourceBase):
    id: int
    fetch_interval: str = "daily"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceTestResult(BaseModel):
    success: bool
    message: str
    fetched_count: int = 0
    sample_items: list[dict] = []


# ==================== Jobs ====================
class DigestJobResponse(BaseModel):
    id: int
    job_date: str
    job_type: str
    status: str
    raw_count: int
    filtered_count: int
    processed_count: int
    email_sent_count: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DigestOutputResponse(BaseModel):
    id: int
    digest_job_id: int
    title: str
    summary: Optional[str] = None
    json_content: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Logs ====================
class RawItemResponse(BaseModel):
    id: int
    source_id: int
    title: str
    url: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    status: str
    extra_data: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessedItemResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    importance: int
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmailLogResponse(BaseModel):
    id: int
    digest_job_id: Optional[int] = None
    recipient_email: str
    subject: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LLMCallLogResponse(_BaseSchema):
    id: int
    digest_job_id: Optional[int] = None
    provider_type: Optional[str] = None
    model_name: Optional[str] = None
    status: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SourceFetchLogResponse(BaseModel):
    id: int
    source_id: int
    status: str
    fetched_count: int
    new_count: int
    http_status_code: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Email Template ====================
class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    subject_template: str
    html_template: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateUpdate(BaseModel):
    subject_template: Optional[str] = None
    html_template: Optional[str] = None
    is_active: Optional[bool] = None


class EmailPreviewRequest(BaseModel):
    pass


# ==================== Schedule Config ====================
class ScheduleConfigResponse(BaseModel):
    id: int
    enabled: bool
    timezone: str
    fetch_time: str
    digest_time: str
    send_time: str
    weekdays_only: bool
    retry_count: int
    retry_interval_minutes: int

    class Config:
        from_attributes = True


class ScheduleConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    timezone: Optional[str] = None
    fetch_time: Optional[str] = None
    digest_time: Optional[str] = None
    send_time: Optional[str] = None
    weekdays_only: Optional[bool] = None
    retry_count: Optional[int] = None
    retry_interval_minutes: Optional[int] = None


# ==================== Job Actions ====================
class JobActionResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[int] = None
