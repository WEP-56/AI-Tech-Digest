"""收件人配置路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Recipient
from app.schemas import RecipientCreate, RecipientUpdate, RecipientResponse
from app.services.auth_service import get_current_user
from app.services.mail_service import send_test_email

router = APIRouter(prefix="/api/admin/recipients", tags=["收件人配置"])


@router.get("", response_model=list[RecipientResponse])
def list_recipients(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Recipient).order_by(Recipient.created_at.desc()).all()


@router.post("", response_model=RecipientResponse)
def create_recipient(req: RecipientCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    recipient = Recipient(**req.model_dump())
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


@router.get("/{recipient_id}", response_model=RecipientResponse)
def get_recipient(recipient_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="收件人不存在")
    return r


@router.put("/{recipient_id}", response_model=RecipientResponse)
def update_recipient(recipient_id: int, req: RecipientUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="收件人不存在")
    for key, value in req.model_dump(exclude_unset=True).items():
        setattr(r, key, value)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{recipient_id}")
def delete_recipient(recipient_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="收件人不存在")
    db.delete(r)
    db.commit()
    return {"success": True, "message": "已删除"}


@router.post("/{recipient_id}/send-test")
def send_test_to_recipient(recipient_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="收件人不存在")
    success, msg = send_test_email(db, r.email)
    return {"success": success, "message": "发送成功" if success else msg}
