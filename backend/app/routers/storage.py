"""存储管理路由"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import RawItem, ProcessedItem, EmailLog, LLMCallLog, SourceFetchLog
from app.schemas import (
    RawItemResponse, ProcessedItemResponse, EmailLogResponse,
    LLMCallLogResponse, SourceFetchLogResponse,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/admin", tags=["存储管理"])


@router.get("/raw-items", response_model=list[RawItemResponse])
def list_raw_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: int = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(RawItem)
    if source_id:
        q = q.filter(RawItem.source_id == source_id)
    return q.order_by(RawItem.id.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/processed-items", response_model=list[ProcessedItemResponse])
def list_processed_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return db.query(ProcessedItem).order_by(ProcessedItem.id.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/email-logs", response_model=list[EmailLogResponse])
def list_email_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return db.query(EmailLog).order_by(EmailLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/llm-logs", response_model=list[LLMCallLogResponse])
def list_llm_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return db.query(LLMCallLog).order_by(LLMCallLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/source-fetch-logs", response_model=list[SourceFetchLogResponse])
def list_fetch_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return db.query(SourceFetchLog).order_by(SourceFetchLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()


@router.delete("/storage/cleanup")
def cleanup_storage(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = {}
    deleted["raw_items"] = db.query(RawItem).filter(RawItem.created_at < cutoff).delete()
    deleted["processed_items"] = db.query(ProcessedItem).filter(ProcessedItem.created_at < cutoff).delete()
    deleted["email_logs"] = db.query(EmailLog).filter(EmailLog.created_at < cutoff).delete()
    deleted["llm_call_logs"] = db.query(LLMCallLog).filter(LLMCallLog.created_at < cutoff).delete()
    deleted["source_fetch_logs"] = db.query(SourceFetchLog).filter(SourceFetchLog.created_at < cutoff).delete()
    db.commit()
    total = sum(deleted.values())
    return {"success": True, "message": f"已清理 {total} 条历史数据（{days}天前）", "details": deleted}
