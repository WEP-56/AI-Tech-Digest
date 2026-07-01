"""邮件模板路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EmailTemplate, DigestOutput
from app.schemas import EmailTemplateResponse, EmailTemplateUpdate
from app.services.auth_service import get_current_user
from app.services.email_renderer import render_html, render_subject

router = APIRouter(prefix="/api/admin/email-template", tags=["邮件模板"])


def _get_or_create_template(db: Session) -> EmailTemplate:
    template = db.query(EmailTemplate).filter(EmailTemplate.is_active == True).first()
    if not template:
        template = db.query(EmailTemplate).first()
    if not template:
        template = EmailTemplate(name="default", is_active=True)
        db.add(template)
        db.commit()
        db.refresh(template)
    return template


@router.get("", response_model=EmailTemplateResponse)
def get_template(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return _get_or_create_template(db)


@router.put("", response_model=EmailTemplateResponse)
def update_template(req: EmailTemplateUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    template = _get_or_create_template(db)
    if req.subject_template is not None:
        template.subject_template = req.subject_template
    if req.html_template is not None:
        template.html_template = req.html_template
    if req.is_active is not None:
        template.is_active = req.is_active
    db.commit()
    db.refresh(template)
    return template


@router.post("/preview")
def preview_template(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """预览邮件：使用最新的日报数据"""
    output = db.query(DigestOutput).order_by(DigestOutput.id.desc()).first()
    template = _get_or_create_template(db)
    if not output:
        # 生成预览数据
        sample_data = {
            "title": "AI 前沿日报｜预览",
            "summary": "这是一封预览邮件，展示邮件模板的渲染效果。",
            "sections": [{
                "name": "示例分类",
                "items": [{
                    "title": "示例资讯标题",
                    "summary": "这是示例摘要内容。",
                    "why_it_matters": "这是示例推荐理由。",
                    "source": "示例来源",
                    "url": "https://example.com",
                    "importance": 4,
                    "tags": ["AI", "LLM"],
                }],
            }],
        }
        import json
        html = render_html(sample_data, "预览日期")
        subject = render_subject(template.subject_template, sample_data, "预览日期")
        return {"subject": subject, "html": html}
    import json
    data = json.loads(output.json_content) if output.json_content else {}
    html = render_html(data, output.title.split("|")[-1] if "|" in output.title else "")
    subject = render_subject(template.subject_template, data, "")
    return {"subject": subject, "html": html}


@router.post("/send-preview")
def send_preview(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """发送预览邮件给当前配置的邮箱"""
    from app.services.mail_service import send_test_email
    from app.models import MailAccount
    account = db.query(MailAccount).filter(MailAccount.enabled == True).first()
    if not account:
        raise HTTPException(status_code=400, detail="未配置启用的邮箱账户")
    success, msg = send_test_email(db, account.email)
    return {"success": success, "message": "发送成功" if success else msg}
