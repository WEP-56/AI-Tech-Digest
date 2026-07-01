"""任务路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DigestJob, DigestOutput
from app.schemas import DigestJobResponse, DigestOutputResponse, JobActionResponse
from app.services.auth_service import get_current_user
from app.services.digest_service import run_full_pipeline, generate_digest, send_digest
from app.services.fetcher import fetch_all_sources

router = APIRouter(prefix="/api/admin/jobs", tags=["任务管理"])


@router.get("", response_model=list[DigestJobResponse])
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    offset = (page - 1) * page_size
    return db.query(DigestJob).order_by(DigestJob.id.desc()).offset(offset).limit(page_size).all()


@router.get("/{job_id}", response_model=DigestJobResponse)
def get_job(job_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    job = db.query(DigestJob).filter(DigestJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@router.get("/{job_id}/output", response_model=DigestOutputResponse)
def get_job_output(job_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    output = db.query(DigestOutput).filter(DigestOutput.digest_job_id == job_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="日报内容不存在")
    return output


@router.post("/fetch-now", response_model=JobActionResponse)
def fetch_now(db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.models import DigestJob
    from datetime import datetime
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
        job.filtered_count = result["new_items"]
        job.status = "success"
        job.finished_at = datetime.utcnow()
        db.commit()
        return JobActionResponse(
            success=True,
            message=f"采集完成: 成功 {result['success']}/{result['total']}, 新增 {result['new_items']} 条",
            job_id=job.id,
        )
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        return JobActionResponse(
            success=False,
            message=f"采集失败: {e}",
            job_id=job.id,
        )


@router.post("/generate-digest", response_model=JobActionResponse)
def generate_digest_now(db: Session = Depends(get_db), _=Depends(get_current_user)):
    job = generate_digest(db, job_type="manual")
    return JobActionResponse(
        success=job.status == "success",
        message=f"日报生成{'成功' if job.status == 'success' else '失败'}: {job.error_message or ''}",
        job_id=job.id,
    )


@router.post("/send-now", response_model=JobActionResponse)
def send_now(job_id: int = Query(None), db: Session = Depends(get_db), _=Depends(get_current_user)):
    from app.services.digest_service import send_latest_digest
    from app.models import DigestJob
    from datetime import datetime
    if job_id:
        result = send_digest(db, job_id)
        return JobActionResponse(
            success=result.get("success", False),
            message=f"发送{'成功' if result.get('success') else '失败'}: {result.get('error', '')}",
        )
    else:
        result = send_latest_digest(db)
        # Find the latest job to link
        latest_job = db.query(DigestJob).order_by(DigestJob.id.desc()).first()
        return JobActionResponse(
            success=result.get("success", False),
            message=f"发送{'成功' if result.get('success') else '失败'}: {result.get('error', '')}",
            job_id=latest_job.id if latest_job else None,
        )


@router.post("/run-pipeline", response_model=JobActionResponse)
def run_pipeline(db: Session = Depends(get_db), _=Depends(get_current_user)):
    result = run_full_pipeline(db, job_type="manual")
    return JobActionResponse(
        success=result.get("success", False),
        message=f"完整流程{'成功' if result.get('success') else '失败'}: 采集{result.get('raw_count', 0)}条, "
                f"处理{result.get('processed_count', 0)}条, 发送{result.get('email_sent', 0)}封",
        job_id=result.get("job_id"),
    )
