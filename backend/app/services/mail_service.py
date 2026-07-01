"""邮件发送服务：通过SMTP发送HTML邮件"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import MailAccount, Recipient, EmailLog
from app.security import decrypt_value


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_security: str,
    sender_email: str,
    sender_name: str,
    auth_code: str,
    to_emails: list[str],
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
    subject: str = "",
    html_content: str = "",
    text_content: str = "",
) -> tuple[bool, str]:
    """发送邮件，返回 (success, error_message)"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = ", ".join(to_emails)
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    all_recipients = list(to_emails) + list(cc_emails or []) + list(bcc_emails or [])
    if html_content:
        msg.attach(MIMEText(html_content, "html", "utf-8"))
    if text_content:
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
    elif html_content:
        # 附带纯文本fallback
        msg.attach(MIMEText("请使用支持HTML的邮件客户端查看。", "plain", "utf-8"))

    try:
        if smtp_security == "ssl":
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            if smtp_security == "starttls":
                server.starttls(context=ssl.create_default_context())
        server.login(sender_email, auth_code)
        server.sendmail(sender_email, all_recipients, msg.as_string())
        server.quit()
        return True, ""
    except smtplib.SMTPAuthenticationError as e:
        return False, f"SMTP认证失败: {e}"
    except smtplib.SMTPException as e:
        return False, f"SMTP错误: {e}"
    except Exception as e:
        return False, f"发送失败: {e}"


def _get_usable_mail_account(db: Session) -> MailAccount | None:
    """获取可用的邮箱账户：优先启用且有授权码的，回退到任意有授权码的"""
    # 优先找enabled=True的
    account = db.query(MailAccount).filter(MailAccount.enabled == True).first()
    if account and account.smtp_auth_code_encrypted and account.email:
        return account
    # 回退：找任意有授权码和email的
    accounts = db.query(MailAccount).all()
    for acc in accounts:
        if acc.smtp_auth_code_encrypted and acc.email:
            return acc
    return None


def send_digest_email(
    db: Session,
    digest_job_id: Optional[int],
    html_content: str,
    text_content: str,
    subject: str,
    recipients: list[Recipient] | None = None,
    is_test: bool = False,
) -> dict:
    """发送日报邮件给收件人，返回发送统计"""
    mail_account = _get_usable_mail_account(db)
    if not mail_account:
        return {"success": False, "sent": 0, "failed": 0, "error": "未配置邮箱账户或未填写邮箱地址/授权码"}

    smtp_auth_code = decrypt_value(mail_account.smtp_auth_code_encrypted)
    if not smtp_auth_code:
        return {"success": False, "sent": 0, "failed": 0, "error": "SMTP授权码为空，请先在邮箱配置中填写授权码"}

    # 获取收件人
    if recipients is None:
        recipients = db.query(Recipient).filter(Recipient.enabled == True).all()
    if not recipients:
        return {"success": False, "sent": 0, "failed": 0, "error": "没有启用的收件人"}

    to_emails = [r.email for r in recipients if r.recipient_type == "to"]
    cc_emails = [r.email for r in recipients if r.recipient_type == "cc"]
    bcc_emails = [r.email for r in recipients if r.recipient_type == "bcc"]

    if not to_emails and not cc_emails and not bcc_emails:
        return {"success": False, "sent": 0, "failed": 0, "error": "没有有效的收件人邮箱"}

    success, error = send_email(
        smtp_host=mail_account.smtp_host,
        smtp_port=mail_account.smtp_port,
        smtp_security=mail_account.smtp_security,
        sender_email=mail_account.email,
        sender_name=mail_account.sender_name or "AI Tech Digest",
        auth_code=smtp_auth_code,
        to_emails=to_emails,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )

    now = datetime.utcnow()
    for r in recipients:
        log = EmailLog(
            digest_job_id=digest_job_id,
            recipient_id=r.id,
            recipient_email=r.email,
            subject=subject,
            status="sent" if success else "failed",
            sent_at=now if success else None,
            error_message=error if not success else None,
        )
        db.add(log)

    db.commit()
    if success:
        return {"success": True, "sent": len(recipients), "failed": 0}
    else:
        return {"success": False, "sent": 0, "failed": len(recipients), "error": error}


def send_test_email(db: Session, recipient_email: str) -> tuple[bool, str]:
    """发送测试邮件"""
    mail_account = _get_usable_mail_account(db)
    if not mail_account:
        return False, "未配置邮箱账户或未填写邮箱地址/授权码，请先在邮箱配置页面填写并保存"

    smtp_auth_code = decrypt_value(mail_account.smtp_auth_code_encrypted)
    if not smtp_auth_code:
        return False, "SMTP授权码为空，请先在邮箱配置页面填写授权码"

    subject = "AI Tech Digest Mailer - 测试邮件"
    html = """\
    <div style="font-family:sans-serif;padding:20px;">
    <h2>✅ 测试邮件发送成功</h2>
    <p>这封邮件来自 AI Tech Digest Mailer 系统，说明您的 SMTP 配置正确。</p>
    <p>发送时间：""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
    """
    return send_email(
        smtp_host=mail_account.smtp_host,
        smtp_port=mail_account.smtp_port,
        smtp_security=mail_account.smtp_security,
        sender_email=mail_account.email,
        sender_name=mail_account.sender_name or "AI Tech Digest",
        auth_code=smtp_auth_code,
        to_emails=[recipient_email],
        subject=subject,
        html_content=html,
    )
