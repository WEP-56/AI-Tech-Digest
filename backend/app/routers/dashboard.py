"""Dashboard路由"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import RawItem, DigestJob, Source, Recipient, ModelConfig, MailAccount, EmailLog
from app.schemas import DashboardSummary
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/admin/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), _=Depends(get_current_user)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_raw = db.query(RawItem).filter(RawItem.fetched_at >= today_start).count()
    today_valid = db.query(RawItem).filter(RawItem.fetched_at >= today_start, RawItem.status == "pending").count()
    today_processed = db.query(RawItem).filter(RawItem.fetched_at >= today_start, RawItem.status == "processed").count()
    today_sent = db.query(EmailLog).filter(EmailLog.created_at >= today_start, EmailLog.status == "sent").count()
    today_failed = db.query(EmailLog).filter(EmailLog.created_at >= today_start, EmailLog.status == "failed").count()

    last_job = db.query(DigestJob).order_by(DigestJob.id.desc()).first()
    last_error = None
    if last_job and last_job.status == "failed":
        last_error = last_job.error_message

    enabled_sources = db.query(Source).filter(Source.enabled == True).count()
    enabled_recipients = db.query(Recipient).filter(Recipient.enabled == True).count()
    default_model = db.query(ModelConfig).filter(ModelConfig.is_default == True, ModelConfig.enabled == True).first()
    mail_account = db.query(MailAccount).filter(MailAccount.enabled == True).first()

    return DashboardSummary(
        today_raw_count=today_raw,
        today_valid_count=today_valid,
        today_processed_count=today_processed,
        today_email_sent=today_sent,
        today_email_failed=today_failed,
        last_job_time=last_job.finished_at if last_job else None,
        last_error=last_error,
        enabled_sources=enabled_sources,
        enabled_recipients=enabled_recipients,
        default_model_status="已配置" if default_model else "未配置",
        smtp_status="已配置" if mail_account and mail_account.smtp_auth_code_encrypted else "未配置",
    )
