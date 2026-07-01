"""信源配置路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Source
from app.schemas import SourceCreate, SourceUpdate, SourceResponse, SourceTestResult
from app.services.auth_service import get_current_user
from app.services.fetcher import fetch_source, get_fetcher

router = APIRouter(prefix="/api/admin/sources", tags=["信源配置"])


@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Source).order_by(Source.created_at.desc()).all()


@router.post("", response_model=SourceResponse)
def create_source(req: SourceCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = Source(**req.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="信源不存在")
    return s


@router.put("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, req: SourceUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="信源不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="信源不存在")
    db.delete(s)
    db.commit()
    return {"success": True, "message": "已删除"}


@router.post("/{source_id}/test-fetch", response_model=SourceTestResult)
def test_fetch(source_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    fetcher = get_fetcher(source)
    items, error, http_status = fetcher.fetch(source)
    if error and not items:
        return SourceTestResult(success=False, message=error, fetched_count=0, sample_items=[])
    sample = [{"title": i.get("title", ""), "url": i.get("url", ""), "summary": (i.get("summary") or "")[:100]} for i in items[:5]]
    return SourceTestResult(
        success=True,
        message=f"成功抓取 {len(items)} 条" if items else "抓取成功但无内容",
        fetched_count=len(items),
        sample_items=sample,
    )


@router.post("/{source_id}/enable")
def enable_source(source_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="信源不存在")
    s.enabled = True
    db.commit()
    return {"success": True, "message": "已启用"}


@router.post("/{source_id}/disable")
def disable_source(source_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="信源不存在")
    s.enabled = False
    db.commit()
    return {"success": True, "message": "已禁用"}
