"""邮箱配置路由"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MailAccount
from app.security import encrypt_value, decrypt_value, mask_value
from app.schemas import MailAccountCreate, MailAccountUpdate, MailAccountResponse
from app.services.auth_service import get_current_user
from app.services.mail_service import send_email

router = APIRouter(prefix="/api/admin/mail-account", tags=["邮箱配置"])


def _to_response(account: MailAccount) -> MailAccountResponse:
    return MailAccountResponse(
        id=account.id,
        email=account.email,
        sender_name=account.sender_name,
        smtp_host=account.smtp_host,
        smtp_port=account.smtp_port,
        smtp_security=account.smtp_security,
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        imap_security=account.imap_security,
        enabled=account.enabled,
        smtp_auth_code_masked=mask_value(decrypt_value(account.smtp_auth_code_encrypted)),
        imap_auth_code_masked=mask_value(decrypt_value(account.imap_auth_code_encrypted)) if account.imap_auth_code_encrypted else "",
        has_smtp_auth_code=bool(account.smtp_auth_code_encrypted),
        has_imap_auth_code=bool(account.imap_auth_code_encrypted),
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.get("", response_model=list[MailAccountResponse])
def list_accounts(db: Session = Depends(get_db), _=Depends(get_current_user)):
    accounts = db.query(MailAccount).all()
    return [_to_response(a) for a in accounts]


@router.post("", response_model=MailAccountResponse)
def create_account(req: MailAccountCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    account = MailAccount(
        email=req.email,
        sender_name=req.sender_name,
        smtp_host=req.smtp_host,
        smtp_port=req.smtp_port,
        smtp_security=req.smtp_security,
        smtp_auth_code_encrypted=encrypt_value(req.smtp_auth_code),
        imap_host=req.imap_host,
        imap_port=req.imap_port,
        imap_security=req.imap_security,
        imap_auth_code_encrypted=encrypt_value(req.imap_auth_code) if req.imap_auth_code else "",
        enabled=req.enabled,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _to_response(account)


@router.put("/{account_id}", response_model=MailAccountResponse)
def update_account(account_id: int, req: MailAccountUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="邮箱配置不存在")
    if req.email is not None:
        account.email = req.email
    if req.sender_name is not None:
        account.sender_name = req.sender_name
    if req.smtp_host is not None:
        account.smtp_host = req.smtp_host
    if req.smtp_port is not None:
        account.smtp_port = req.smtp_port
    if req.smtp_security is not None:
        account.smtp_security = req.smtp_security
    if req.smtp_auth_code is not None:
        account.smtp_auth_code_encrypted = encrypt_value(req.smtp_auth_code)
    if req.imap_host is not None:
        account.imap_host = req.imap_host
    if req.imap_port is not None:
        account.imap_port = req.imap_port
    if req.imap_security is not None:
        account.imap_security = req.imap_security
    if req.imap_auth_code is not None:
        account.imap_auth_code_encrypted = encrypt_value(req.imap_auth_code)
    if req.enabled is not None:
        account.enabled = req.enabled
    db.commit()
    db.refresh(account)
    return _to_response(account)


@router.post("/{account_id}/test-smtp")
def test_smtp(account_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="邮箱配置不存在")
    if not account.smtp_host:
        return {"success": False, "message": "SMTP主机地址为空，请填写后再测试"}
    if not account.email:
        return {"success": False, "message": "发件邮箱地址为空，请填写后再测试"}
    auth_code = decrypt_value(account.smtp_auth_code_encrypted)
    if not auth_code:
        return {"success": False, "message": "SMTP授权码为空，请填写QQ邮箱授权码后再测试"}
    try:
        import smtplib, ssl
        if account.smtp_security == "ssl":
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(account.smtp_host, account.smtp_port, context=context, timeout=15)
        else:
            server = smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=15)
            if account.smtp_security == "starttls":
                server.starttls(context=ssl.create_default_context())
        server.login(account.email, auth_code)
        server.quit()
        return {"success": True, "message": "SMTP连接测试成功"}
    except smtplib.SMTPAuthenticationError as e:
        return {"success": False, "message": f"SMTP认证失败：邮箱地址或授权码不正确。请检查QQ邮箱授权码是否正确（{e}）"}
    except smtplib.SMTPConnectError as e:
        return {"success": False, "message": f"SMTP连接失败：无法连接到 {account.smtp_host}:{account.smtp_port}，请检查网络或防火墙设置（{e}）"}
    except Exception as e:
        error_type = type(e).__name__
        return {"success": False, "message": f"SMTP连接测试失败 ({error_type}): {e}"}


@router.post("/{account_id}/send-test")
def send_test(account_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="邮箱配置不存在")
    auth_code = decrypt_value(account.smtp_auth_code_encrypted)
    if not auth_code:
        return {"success": False, "message": "SMTP授权码为空"}
    subject = "AI Tech Digest Mailer - 测试邮件"
    html = f'<div style="font-family:sans-serif;padding:20px;"><h2>测试邮件</h2><p>发送时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p></div>'
    success, error = send_email(
        account.smtp_host, account.smtp_port, account.smtp_security,
        account.email, account.sender_name or "AI Tech Digest", auth_code,
        [account.email], subject=subject, html_content=html,
    )
    return {"success": success, "message": "发送成功" if success else error}
