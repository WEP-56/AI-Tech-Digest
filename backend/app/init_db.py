"""数据库初始化：创建表、默认管理员、默认配置、预设信源"""
from app.database import engine, Base, SessionLocal
from app.models import AdminUser, ScheduleConfig, EmailTemplate, MailAccount, Source
from app.security import hash_password, encrypt_value
from app.config import settings


# QQ邮箱默认配置（用户只需填入授权码即可使用）
DEFAULT_MAIL_ACCOUNT = {
    "email": "",  # 用户需要填写自己的QQ邮箱
    "sender_name": "AI Tech Digest",
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_security": "ssl",
    "imap_host": "imap.qq.com",
    "imap_port": 993,
    "imap_security": "ssl",
    "enabled": False,  # 未填授权码前不启用
}

# 预设信源（用户可删改）
DEFAULT_SOURCES = [
    {
        "name": "Hacker News",
        "source_type": "hackernews_rss",
        "url": "https://news.ycombinator.com/rss",
        "category": "技术社区",
        "language": "en",
        "include_keywords": "AI,LLM,agent,GPT,claude,openai,anthropic,model,inference,RAG,MCP",
        "exclude_keywords": "",
        "max_items": 30,
        "weight": 1.5,
        "enabled": True,
        "send_to_llm": True,
    },
    {
        "name": "GitHub Trending - AI/LLM",
        "source_type": "github_trending",
        "url": "https://github.com/trending",
        "category": "开源项目",
        "language": "en",
        "include_keywords": "llm,agent,rag,mcp,ai,inference,coding,workflow",
        "exclude_keywords": "",
        "github_language": "",  # 不限语言
        "github_since": "daily",
        "min_stars": 50,
        "max_items": 20,
        "weight": 1.3,
        "enabled": True,
        "send_to_llm": True,
    },
    {
        "name": "OpenAI Blog",
        "source_type": "rss",
        "url": "https://openai.com/blog/rss.xml",
        "category": "AI厂商动态",
        "language": "en",
        "include_keywords": "",
        "exclude_keywords": "",
        "max_items": 15,
        "weight": 1.4,
        "enabled": True,
        "send_to_llm": True,
    },
    {
        "name": "The Verge - AI",
        "source_type": "rss",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "AI厂商动态",
        "language": "en",
        "include_keywords": "",
        "exclude_keywords": "",
        "max_items": 15,
        "weight": 1.3,
        "enabled": True,
        "send_to_llm": True,
    },
    {
        "name": "InfoQ 中文站",
        "source_type": "rss",
        "url": "https://www.infoq.cn/feed",
        "category": "中文AI媒体",
        "language": "zh",
        "include_keywords": "",
        "exclude_keywords": "",
        "max_items": 20,
        "weight": 1.2,
        "enabled": True,
        "send_to_llm": True,
    },
    {
        "name": "V2EX - 节点分享",
        "source_type": "rss",
        "url": "https://www.v2ex.com/index.xml",
        "category": "技术社区",
        "language": "zh",
        "include_keywords": "AI,LLM,GPT,大模型,智能,算法",
        "exclude_keywords": "",
        "max_items": 15,
        "weight": 1.0,
        "enabled": False,  # 默认禁用，信息较杂
        "send_to_llm": True,
    },
]


def init_database():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 创建默认管理员
        if not db.query(AdminUser).first():
            admin = AdminUser(
                username=settings.DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                is_active=True,
                must_change_password=True,
            )
            db.add(admin)
            print(f"[ok] Created default admin: {admin.username} / {settings.DEFAULT_ADMIN_PASSWORD}")

        # 创建默认邮箱配置（QQ邮箱参数，授权码留空）
        if not db.query(MailAccount).first():
            mail = MailAccount(
                email=DEFAULT_MAIL_ACCOUNT["email"],
                sender_name=DEFAULT_MAIL_ACCOUNT["sender_name"],
                smtp_host=DEFAULT_MAIL_ACCOUNT["smtp_host"],
                smtp_port=DEFAULT_MAIL_ACCOUNT["smtp_port"],
                smtp_security=DEFAULT_MAIL_ACCOUNT["smtp_security"],
                smtp_auth_code_encrypted="",  # 用户需填入QQ邮箱授权码
                imap_host=DEFAULT_MAIL_ACCOUNT["imap_host"],
                imap_port=DEFAULT_MAIL_ACCOUNT["imap_port"],
                imap_security=DEFAULT_MAIL_ACCOUNT["imap_security"],
                imap_auth_code_encrypted="",
                enabled=DEFAULT_MAIL_ACCOUNT["enabled"],
            )
            db.add(mail)
            print("[ok] Created default QQ mail account config")

        # 创建默认调度配置
        if not db.query(ScheduleConfig).first():
            config = ScheduleConfig()
            db.add(config)

        # 创建默认邮件模板
        if not db.query(EmailTemplate).first():
            template = EmailTemplate(name="default", is_active=True)
            db.add(template)

        # 创建预设信源
        existing_sources = db.query(Source).count()
        if existing_sources == 0:
            for src_data in DEFAULT_SOURCES:
                source = Source(**src_data)
                db.add(source)
            print(f"[ok] Created {len(DEFAULT_SOURCES)} default sources")

        db.commit()
        print("[ok] Database initialized")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
