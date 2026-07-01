"""邮件HTML渲染器：将日报JSON渲染为HTML邮件"""
import json
import html
from datetime import datetime


DEFAULT_SUBJECT_TEMPLATE = "{{date}} AI 前沿日报"

# 内联CSS的HTML邮件模板
DEFAULT_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:20px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;max-width:640px;width:100%;">

<!-- Header -->
<tr>
<td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:30px 40px;">
<h1 style="margin:0;color:#fff;font-size:22px;font-weight:600;">🤖 {{digest_title}}</h1>
<p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">{{date}} · AI Tech Digest Mailer</p>
</td>
</tr>

<!-- Summary -->
<tr><td style="padding:24px 40px 0;">
<div style="background:#f0f4ff;border-radius:8px;padding:16px 20px;">
<p style="margin:0;color:#333;font-size:14px;line-height:1.6;">📋 <strong>今日摘要</strong></p>
<p style="margin:8px 0 0;color:#555;font-size:13px;line-height:1.7;">{{summary}}</p>
</div>
</td></tr>

<!-- Sections -->
{% for section in sections %}
<tr><td style="padding:20px 40px 0;">
<h2 style="margin:0 0 12px;font-size:16px;color:#333;border-bottom:2px solid #667eea;padding-bottom:8px;">{{section.name}}</h2>
{% for item in section['items'] %}
<div style="margin-bottom:16px;padding:16px;background:#f9fafb;border-radius:6px;border-left:3px solid {{importance_color(item.importance)}};">
<div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
<h3 style="margin:0;font-size:14px;color:#333;font-weight:600;flex:1;">{{loop.index}}. {{item.title}}</h3>
{% if item.importance >= 4 %}
<span style="background:#ff4757;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px;white-space:nowrap;">🔥 重点</span>
{% elif item.importance == 3 %}
<span style="background:#ffa502;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px;white-space:nowrap;">值得关注</span>
{% endif %}
</div>
<p style="margin:0 0 8px;color:#555;font-size:13px;line-height:1.6;">{{item.summary}}</p>
{% if item.why_it_matters %}
<p style="margin:0 0 8px;color:#666;font-size:12px;line-height:1.6;"><strong style="color:#667eea;">为什么值得关注：</strong>{{item.why_it_matters}}</p>
{% endif %}
<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
<span style="color:#999;font-size:11px;">来源：{{item.source}}</span>
{% if item.tags %}
{% for tag in item.tags %}
<span style="background:#e8eaf6;color:#3f51b5;font-size:10px;padding:1px 6px;border-radius:3px;">{{tag}}</span>
{% endfor %}
{% endif %}
</div>
{% if item.url and item.url.strip() %}
<a href="{{item.url}}" style="display:inline-block;margin-top:8px;color:#667eea;font-size:12px;text-decoration:none;">阅读原文 →</a>
{% endif %}
</div>
{% endfor %}
</td></tr>
{% endfor %}

<!-- Footer -->
<tr><td style="padding:20px 40px 30px;">
<hr style="border:none;border-top:1px solid #eee;margin:0 0 16px;">
<p style="margin:0;color:#999;font-size:11px;line-height:1.6;text-align:center;">
本邮件由 AI Tech Digest Mailer 自动生成发送<br>
如需退订或修改订阅，请联系管理员
</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def _importance_color(importance: int) -> str:
    colors = {5: "#ff4757", 4: "#ff4757", 3: "#ffa502", 2: "#7bed9f", 1: "#a4b0be"}
    return colors.get(importance, "#a4b0be")


def render_subject(subject_template: str, digest_data: dict, date_str: str = "") -> str:
    """渲染邮件标题"""
    template = subject_template or DEFAULT_SUBJECT_TEMPLATE
    top_topic = ""
    if digest_data.get("sections"):
        sections = digest_data["sections"]
        if sections and sections[0].get("items"):
            top_topic = sections[0]["items"][0].get("title", "")[:30]
    return (
        template
        .replace("{{date}}", date_str)
        .replace("{{digest_title}}", digest_data.get("title", "AI 前沿日报"))
        .replace("{{top_topic}}", top_topic)
    )


def render_html(digest_data: dict, date_str: str = "") -> str:
    """将日报JSON渲染为HTML邮件"""
    from jinja2 import Template

    sections = digest_data.get("sections", [])
    template_str = DEFAULT_HTML_TEMPLATE
    template = Template(template_str)
    html_content = template.render(
        digest_title=digest_data.get("title", "AI 前沿日报"),
        date=date_str or datetime.now().strftime("%Y-%m-%d"),
        summary=digest_data.get("summary", ""),
        sections=sections,
        importance_color=_importance_color,
    )
    return html_content


def render_text(digest_data: dict, date_str: str = "") -> str:
    """渲染纯文本版本"""
    lines = [f"{'=' * 50}", f"{digest_data.get('title', 'AI 前沿日报')}", f"日期: {date_str}", "=" * 50, ""]
    if digest_data.get("summary"):
        lines.append(f"摘要: {digest_data['summary']}")
        lines.append("")
    for section in digest_data.get("sections", []):
        lines.append(f"\n--- {section['name']} ---")
        for i, item in enumerate(section.get("items", []), 1):
            lines.append(f"  {i}. {item.get('title', '')}")
            if item.get("summary"):
                lines.append(f"     {item['summary']}")
            if item.get("why_it_matters"):
                lines.append(f"     为什么值得关注: {item['why_it_matters']}")
            if item.get("source"):
                lines.append(f"     来源: {item['source']}")
            if item.get("url"):
                lines.append(f"     链接: {item['url']}")
            lines.append("")
    return "\n".join(lines)


def parse_llm_json(text: str) -> dict:
    """解析LLM返回的JSON，容错处理"""
    text = text.strip()
    # 移除可能的markdown代码块标记
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    # 尝试提取JSON
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start: end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试修复常见问题
        try:
            return json.loads(text.replace("'", '"'))
        except Exception:
            return {"title": "解析失败", "summary": "LLM返回的内容无法解析为JSON", "sections": [], "_raw": text[:1000]}
