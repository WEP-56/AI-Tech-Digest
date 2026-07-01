"""Schedule configuration and manual task triggers."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DigestJob, ScheduleConfig
from app.schemas import JobActionResponse, ScheduleConfigResponse, ScheduleConfigUpdate
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/admin/schedule", tags=["任务调度"])


def _get_or_create_config(db: Session) -> ScheduleConfig:
    config = db.query(ScheduleConfig).first()
    if not config:
        config = ScheduleConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ScheduleConfigResponse)
def get_schedule(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return _get_or_create_config(db)


@router.put("", response_model=ScheduleConfigResponse)
def update_schedule(req: ScheduleConfigUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    config = _get_or_create_config(db)
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)

    try:
        from app.services.scheduler import reload_schedule
        reload_schedule()
    except Exception:
        pass

    return config


@router.post("/trigger-fetch", response_model=JobActionResponse)
def trigger_fetch(db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.services.fetcher import fetch_all_sources

    job = DigestJob(
        job_date=datetime.utcnow().strftime("%Y-%m-%d"),
        job_type="manual",
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        result = fetch_all_sources(db)
        job.raw_count = result["new_items"]
        job.status = "success"
        job.finished_at = datetime.utcnow()
        db.commit()
        return JobActionResponse(
            success=True,
            message=f"采集完成: 成功 {result['success']}/{result['total']}，新增 {result['new_items']} 条",
            job_id=job.id,
        )
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        return JobActionResponse(success=False, message=f"采集失败: {e}", job_id=job.id)


@router.post("/trigger-generate", response_model=JobActionResponse)
def trigger_generate(db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.services.digest_service import generate_digest

    job = generate_digest(db, job_type="manual", auto_fetch=False, allow_recent_fallback=True)
    return JobActionResponse(
        success=job.status == "success",
        message=f"日报生成{'成功' if job.status == 'success' else '失败'}: {job.error_message or ''}",
        job_id=job.id,
    )


@router.post("/trigger-send", response_model=JobActionResponse)
def trigger_send(db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.services.digest_service import send_latest_digest

    result = send_latest_digest(db)
    return JobActionResponse(
        success=result.get("success", False),
        message=f"发送{'成功' if result.get('success') else '失败'}: {result.get('error', '')}",
    )


@router.post("/trigger-pipeline", response_model=JobActionResponse)
def trigger_pipeline(db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.services.digest_service import run_full_pipeline

    result = run_full_pipeline(db, job_type="manual")
    message = (
        f"完整链路{'成功' if result.get('success') else '失败'}: "
        f"采集 {result.get('raw_count', 0)} 条，"
        f"生成 {result.get('processed_count', 0)} 条，"
        f"发送 {result.get('email_sent', 0)} 封"
    )
    if result.get("error"):
        message += f"，错误: {result.get('error')}"
    return JobActionResponse(
        success=result.get("success", False),
        message=message,
        job_id=result.get("job_id"),
    )
