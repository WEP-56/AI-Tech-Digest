"""日报生成服务：整合采集、过滤、LLM总结、渲染"""
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    Source, RawItem, ProcessedItem, DigestJob, DigestOutput,
    LLMCallLog, ModelConfig, EmailTemplate, SourceFetchLog,
)
from app.security import decrypt_value
from app.services.llm_client import create_llm_client
from app.services.email_renderer import render_html, render_text, render_subject, parse_llm_json
from app.services.fetcher import fetch_all_sources


SYSTEM_PROMPT = """你是一个专业的技术资讯分析助手，负责将多来源、杂乱的技术信息整理成一份适合技术人员阅读的中文日报。

要求：
1. 使用中文输出。
2. 不要机械翻译标题。
3. 合并重复或相似信息。
4. 优先保留 AI、LLM、Agent、RAG、MCP、开源项目、开发者工具、云计算相关内容。
5. 每条内容必须包含标题、摘要、为什么值得关注、来源、链接和重要性评分。
6. 不得编造输入中不存在的信息。
7. 如果原始信息不足，请标记为"信息有限"。
8. 输出必须是合法 JSON。
9. 不要输出 Markdown。
10. 不要输出 JSON 以外的解释性文字。"""

USER_PROMPT_TEMPLATE = """以下是今天采集到的技术资讯，请生成中文技术日报。

资讯列表：
{items}

请严格按照以下 JSON 结构输出：

{{
  "title": "AI 前沿日报|{date}",
  "summary": "今日重点关注内容概述",
  "sections": [
    {{
      "name": "分类名称",
      "items": [
        {{
          "title": "标题",
          "summary": "简短总结",
          "why_it_matters": "为什么值得关注",
          "source": "来源名称",
          "url": "链接",
          "importance": 1,
          "tags": ["标签"]
        }}
      ]
    }}
  ]
}}

重要性评分：1=普通, 2=可读, 3=值得关注, 4=重要, 5=今日重点
请将内容按分类分组（如：AI模型动态、开源项目、开发者工具等）。"""


def _format_items_for_llm(raw_items: list[RawItem], sources: list[Source]) -> str:
    """将原始资讯格式化为LLM输入文本"""
    source_map = {s.id: s for s in sources}
    lines = []
    for i, item in enumerate(raw_items, 1):
        source = source_map.get(item.source_id)
        source_name = source.name if source else "未知"
        category = source.category if source else ""
        extra = ""
        if item.extra_data:
            stars = item.extra_data.get("stars")
            if stars:
                extra = f" [Stars: {stars}]"
        lines.append(
            f"{i}. 标题: {item.title}\n"
            f"   来源: {source_name} ({category})\n"
            f"   链接: {item.url or '无'}\n"
            f"   摘要: {item.summary or '无'}{extra}"
        )
    return "\n".join(lines)


def _filter_and_sort_items(
    db: Session,
    time_window_hours: int = 24,
    max_items: int = 50,
    statuses: tuple[str, ...] = ("pending",),
) -> list[RawItem]:
    """过滤和排序原始资讯"""
    cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
    enabled_source_ids = [
        s.id for s in db.query(Source).filter(
            Source.enabled == True,
            Source.send_to_llm == True,
        ).all()
    ]
    if not enabled_source_ids:
        return []
    query = db.query(RawItem).filter(
        RawItem.status.in_(statuses),
        RawItem.fetched_at >= cutoff,
        RawItem.source_id.in_(enabled_source_ids),
    )
    # 关联source获取权重
    items = query.all()
    sources = db.query(Source).all()
    source_map = {s.id: s for s in sources}

    def sort_key(item):
        source = source_map.get(item.source_id)
        weight = source.weight if source else 1.0
        published = item.published_at or datetime.min
        freshness = (datetime.utcnow() - published).total_seconds() / 3600  # 小时
        return -(weight * 10 - freshness * 0.1)  # 权重高优先，新鲜的优先

    items.sort(key=sort_key)
    return items[:max_items]


def _fallback_digest_from_raw_items(raw_items: list[RawItem], date_str: str, summary: str) -> dict:
    """Build a readable digest from source items when the model is unavailable or returns bad JSON."""
    return {
        "title": f"AI 前沿日报|{date_str}",
        "summary": summary,
        "sections": [{
            "name": "原始资讯",
            "items": [
                {
                    "title": item.title,
                    "summary": item.summary or item.content or "",
                    "why_it_matters": "信息有限，保留原始资讯供人工判断。",
                    "source": item.source.name if item.source else "",
                    "url": item.url or "",
                    "importance": 1,
                    "tags": [],
                }
                for item in raw_items[:20]
            ],
        }],
    }


def generate_digest(db: Session, job_type: str = "daily") -> DigestJob:
    """生成日报：采集 -> 过滤 -> LLM总结 -> 渲染"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    job = DigestJob(
        job_date=date_str,
        job_type=job_type,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # 1. 采集（如果是daily则自动采集，manual则用已有数据）
        if job_type == "daily":
            fetch_results = fetch_all_sources(db)
        else:
            fetch_results = {"total": 0, "success": 0, "failed": 0, "new_items": 0}

        # 2. 过滤排序
        raw_items = _filter_and_sort_items(db, max_items=50)
        if len(raw_items) < 20:
            seen_item_ids = {item.id for item in raw_items}
            recent_processed_items = _filter_and_sort_items(
                db,
                time_window_hours=72,
                max_items=50,
                statuses=("processed",),
            )
            raw_items.extend(
                item for item in recent_processed_items
                if item.id not in seen_item_ids
            )
            raw_items = raw_items[:50]
        job.raw_count = db.query(RawItem).filter(RawItem.fetched_at >= datetime.utcnow() - timedelta(hours=24)).count()
        job.filtered_count = len(raw_items)
        model_config = None

        if not raw_items:
            digest_data = {
                "title": f"AI 前沿日报|{date_str}",
                "summary": "今日信息有限，未采集到足够的资讯内容。",
                "sections": [],
            }
        else:
            # 3. 获取默认模型
            model_config = db.query(ModelConfig).filter(
                ModelConfig.is_default == True, ModelConfig.enabled == True
            ).first()
            if not model_config:
                model_config = db.query(ModelConfig).filter(ModelConfig.enabled == True).first()

            if not model_config:
                digest_data = _fallback_digest_from_raw_items(
                    raw_items,
                    date_str,
                    "未配置可用 LLM 模型，已保留原始资讯供阅读。",
                )

            elif False:
                digest_data = {
                    "title": f"AI 前沿日报|{date_str}",
                    "summary": "未配置LLM模型，无法生成日报摘要。请先在模型配置页面添加并启用模型。",
                    "sections": [{"name": "原始资讯", "items": [
                        {"title": item.title, "summary": item.summary or "", "why_it_matters": "",
                         "source": item.extra_data.get("repo_full_name", "") if item.extra_data else "",
                         "url": item.url or "", "importance": 1, "tags": []}
                        for item in raw_items[:20]
                    ]}],
                }
            else:
                # 4. 调用LLM
                sources = db.query(Source).all()
                items_text = _format_items_for_llm(raw_items, sources)
                user_prompt = USER_PROMPT_TEMPLATE.format(items=items_text, date=date_str)

                api_key = decrypt_value(model_config.api_key_encrypted)
                config = {
                    "provider_type": model_config.provider_type,
                    "base_url": model_config.base_url,
                    "api_key": api_key,
                    "model_name": model_config.model_name,
                    "temperature": model_config.temperature,
                    "max_output_tokens": model_config.max_output_tokens,
                    "timeout_seconds": model_config.timeout_seconds,
                    "retry_count": model_config.retry_count,
                    "anthropic_version": model_config.anthropic_version,
                }

                llm_start = time.time()
                client = create_llm_client(config)
                result = client.generate(SYSTEM_PROMPT, user_prompt)
                llm_latency = int((time.time() - llm_start) * 1000)

                # 记录LLM调用日志
                llm_log = LLMCallLog(
                    digest_job_id=job.id,
                    model_config_id=model_config.id,
                    provider_type=model_config.provider_type,
                    model_name=model_config.model_name,
                    status="success" if result.success else "failed",
                    input_tokens=result.usage.get("input_tokens") or result.usage.get("prompt_tokens"),
                    output_tokens=result.usage.get("output_tokens") or result.usage.get("completion_tokens"),
                    latency_ms=llm_latency,
                    error_message=result.error if not result.success else None,
                )
                db.add(llm_log)

                if result.success:
                    digest_data = parse_llm_json(result.text)
                    if digest_data.get("_parse_error") or not digest_data.get("sections"):
                        digest_data = _fallback_digest_from_raw_items(
                            raw_items,
                            date_str,
                            "LLM 返回内容无法解析为有效日报结构，已保留原始资讯供阅读。",
                        )
                else:
                    digest_data = {
                        "title": f"AI 前沿日报|{date_str}",
                        "summary": f"LLM调用失败: {result.error}",
                        "sections": [{"name": "原始资讯", "items": [
                            {"title": item.title, "summary": item.summary or "", "why_it_matters": "",
                             "source": "", "url": item.url or "", "importance": 1, "tags": []}
                            for item in raw_items[:20]
                        ]}],
                    }

        # 5. 渲染
        html_content = render_html(digest_data, date_str)
        text_content = render_text(digest_data, date_str)

        # 6. 保存输出
        output = DigestOutput(
            digest_job_id=job.id,
            title=digest_data.get("title", f"AI 前沿日报|{date_str}"),
            summary=digest_data.get("summary", ""),
            json_content=json.dumps(digest_data, ensure_ascii=False),
            html_content=html_content,
            text_content=text_content,
        )
        db.add(output)

        # 7. 保存处理后的资讯条目
        for section in digest_data.get("sections", []):
            for item in section.get("items", []):
                processed = ProcessedItem(
                    digest_job_id=job.id,
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    why_it_matters=item.get("why_it_matters", ""),
                    category=section.get("name", ""),
                    tags=json.dumps(item.get("tags", []), ensure_ascii=False),
                    importance=item.get("importance", 1),
                    source_name=item.get("source", ""),
                    source_url=item.get("url", ""),
                    llm_model=model_config.model_name if model_config else None,
                )
                db.add(processed)
                # 更新raw_items状态
                job.processed_count += 1

        # 更新raw_items状态
        db.query(RawItem).filter(RawItem.status == "pending").update({RawItem.status: "processed"})

        job.status = "success"
        job.finished_at = datetime.utcnow()
        db.commit()
        return job

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
        return job


def send_digest(db: Session, job_id: int) -> dict:
    """发送指定任务的日报邮件"""
    from app.services.mail_service import send_digest_email

    job = db.query(DigestJob).filter(DigestJob.id == job_id).first()
    if not job:
        return {"success": False, "error": "任务不存在"}
    output = db.query(DigestOutput).filter(DigestOutput.digest_job_id == job_id).first()
    if not output:
        return {"success": False, "error": "日报内容不存在"}

    # 获取邮件模板
    template = db.query(EmailTemplate).filter(EmailTemplate.is_active == True).first()
    subject_template = template.subject_template if template else "{{date}} AI 前沿日报"
    date_str = job.job_date
    digest_data = json.loads(output.json_content) if output.json_content else {}
    subject = render_subject(subject_template, digest_data, date_str)

    result = send_digest_email(
        db=db,
        digest_job_id=job_id,
        html_content=output.html_content or "",
        text_content=output.text_content or "",
        subject=subject,
    )

    if result.get("success"):
        job.email_sent_count = result.get("sent", 0)
        db.commit()

    return result


def run_full_pipeline(db: Session, job_type: str = "daily") -> dict:
    """执行完整流程：采集 -> 生成日报 -> 发送邮件"""
    job = generate_digest(db, job_type)
    if job.status != "success":
        return {"success": False, "job_id": job.id, "error": job.error_message or "日报生成失败"}

    send_result = send_digest(db, job.id)
    return {
        "success": send_result.get("success", False),
        "job_id": job.id,
        "raw_count": job.raw_count,
        "filtered_count": job.filtered_count,
        "processed_count": job.processed_count,
        "email_sent": send_result.get("sent", 0),
        "email_failed": send_result.get("failed", 0),
        "error": send_result.get("error", ""),
    }


def fetch_all_sources_only(db: Session) -> dict:
    """仅执行采集，不生成日报"""
    return fetch_all_sources(db)


def send_latest_digest(db: Session) -> dict:
    """发送最近一次成功的日报"""
    job = db.query(DigestJob).filter(
        DigestJob.status.in_(["success", "partial_success"])
    ).order_by(DigestJob.id.desc()).first()
    if not job:
        return {"success": False, "error": "没有可发送的日报"}
    return send_digest(db, job.id)
