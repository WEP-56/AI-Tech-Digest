"""认证路由"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AdminUser
from app.security import create_access_token, hash_password, verify_password
from app.schemas import LoginRequest, ChangePasswordRequest, Token, AdminUserResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/admin/auth", tags=["认证"])


@router.post("/login", response_model=Token)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")

    token = create_access_token({"sub": user.username})
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = request.client.host if request.client else None
    db.commit()
    return Token(access_token=token, must_change_password=user.must_change_password)


@router.post("/logout")
def logout(current_user: AdminUser = Depends(get_current_user)):
    return {"success": True, "message": "已退出登录"}


@router.get("/me", response_model=AdminUserResponse)
def me(current_user: AdminUser = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码至少6位")
    current_user.password_hash = hash_password(req.new_password)
    current_user.must_change_password = False
    db.commit()
    return {"success": True, "message": "密码修改成功"}
