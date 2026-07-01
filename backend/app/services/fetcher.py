"""信息采集器：RSS、GitHub Trending、网页"""
import re
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import Source, RawItem, SourceFetchLog
from app.security import sha256_hash


def _parse_date(date_str: str) -> Optional[datetime]:
    """尝试解析多种日期格式"""
    if not date_str:
        return None
    # feedparser 已将日期解析为 time.struct_time
    try:
        import time as _time
        t = _time.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z") if isinstance(date_str, str) else None
        if t:
            return datetime(*t[:6])
    except Exception:
        pass
    try:
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except Exception:
        return None


def _clean_html(html: str) -> str:
    """去除HTML标签，保留纯文本"""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(strip=True)[:2000]


class RSSFetcher:
    """RSS信源采集器"""

    def fetch(self, source: Source) -> tuple[list[dict], str, Optional[int]]:
        """返回 (items, error_message, http_status)"""
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(source.url, headers={"User-Agent": "AI-Tech-Digest-Mailer/1.0"})
            if resp.status_code != 200:
                return [], f"HTTP {resp.status_code}", resp.status_code
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:source.max_items]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                link = entry.get("link", "")
                summary_raw = entry.get("summary", "") or entry.get("description", "")
                summary = _clean_html(summary_raw)[:500]
                published = entry.get("published", "") or entry.get("updated", "")
                published_at = _parse_date(published)
                author = entry.get("author", "")
                content_raw = ""
                if source.need_full_text:
                    for key in ("content", "content_value"):
                        if key in entry:
                            content_raw = _clean_html(entry[key][0].get("value", "") if isinstance(entry[key], list) else str(entry[key]))
                            break
                items.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "content": content_raw,
                    "published_at": published_at,
                    "author": author,
                    "source_name": source.name,
                })
            return items, "", resp.status_code
        except Exception as e:
            return [], str(e), None


class GitHubTrendingFetcher:
    """GitHub Trending采集器（通过网页解析）"""

    def fetch(self, source: Source) -> tuple[list[dict], str, Optional[int]]:
        try:
            url = "https://github.com/trending"
            params = {}
            if source.github_language:
                params["l"] = source.github_language
            if source.github_since:
                params["since"] = source.github_since
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(url, params=params, headers={"User-Agent": "AI-Tech-Digest-Mailer/1.0"})
            if resp.status_code != 200:
                return [], f"HTTP {resp.status_code}", resp.status_code
            soup = BeautifulSoup(resp.text, "html.parser")
            items = []
            repos = soup.select("article.Box-row")
            for repo in repos[:source.max_items]:
                h2 = repo.select_one("h2 a")
                if not h2:
                    continue
                repo_path = h2.get("href", "").strip().lstrip("/")
                repo_url = f"https://github.com{h2.get('href', '')}"
                repo_name = repo_path.split("/")[-1] if "/" in repo_path else repo_path
                desc_el = repo.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""
                lang_el = repo.select_one("[itemprop='programmingLanguage']")
                lang = lang_el.get_text(strip=True) if lang_el else ""
                # Stars - 使用更通用的选择器：href包含/stargazers的链接
                stars_el = repo.select("a[href*='/stargazers']")
                stars_text = ""
                for el in stars_el:
                    stars_text = el.get_text(strip=True).replace(",", "").replace(" ", "")
                    break
                if not stars_text:
                    # 回退：尝试旧选择器
                    stars_el2 = repo.select("a.Link.Link--muted")
                    for el in stars_el2:
                        t = el.get_text(strip=True).replace(",", "")
                        if t.isdigit():
                            stars_text = t
                            break
                stars = int(stars_text) if stars_text and stars_text.isdigit() else 0
                if source.min_stars and stars < source.min_stars:
                    continue
                # Today stars
                today_el = repo.select_one("span.d-inline-block.float-sm-right")
                today_stars = today_el.get_text(strip=True) if today_el else ""
                items.append({
                    "title": f"GitHub: {repo_path}",
                    "url": repo_url,
                    "summary": description,
                    "content": "",
                    "published_at": datetime.utcnow(),
                    "author": repo_path.split("/")[0] if "/" in repo_path else "",
                    "source_name": source.name,
                    "extra_data": {
                        "repo_name": repo_name,
                        "repo_full_name": repo_path,
                        "description": description,
                        "language": lang,
                        "stars": stars,
                        "today_stars": today_stars,
                    },
                })
            return items, "", resp.status_code
        except Exception as e:
            return [], str(e), None


def get_fetcher(source: Source):
    """根据信源类型返回对应的采集器"""
    fetchers = {
        "rss": RSSFetcher,
        "github_trending": GitHubTrendingFetcher,
        "hackernews_rss": RSSFetcher,  # HN也用RSS格式
        "arxiv_rss": RSSFetcher,
    }
    return fetchers.get(source.source_type, RSSFetcher)()


def fetch_source(db: Session, source: Source) -> SourceFetchLog:
    """采集单个信源，写入raw_items并返回日志"""
    log = SourceFetchLog(
        source_id=source.id,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(log)
    db.flush()

    fetcher = get_fetcher(source)
    items, error, http_status = fetcher.fetch(source)

    log.http_status_code = http_status
    log.fetched_count = len(items)
    new_count = 0

    if error and not items:
        log.status = "failed"
        log.error_message = error
        log.finished_at = datetime.utcnow()
        db.commit()
        return log

    for item in items:
        title = item.get("title", "")
        url = item.get("url", "")
        url_hash = sha256_hash(url) if url else None
        title_hash = sha256_hash(title) if title else None

        # 去重：URL hash 或 title hash 已存在
        exists = False
        if url_hash:
            exists = db.query(RawItem).filter(RawItem.url_hash == url_hash).first() is not None
        if not exists and title_hash:
            exists = db.query(RawItem).filter(RawItem.title_hash == title_hash).first() is not None
        if exists:
            continue

        # 关键词过滤
        include_kw = source.include_keywords or ""
        include_kw = source.include_keywords or ""
        exclude_kw = source.exclude_keywords or ""
        search_text = (title + " " + item.get("summary", "")).lower()
        if exclude_kw:
            excluded = False
            for kw in exclude_kw.split(","):
                kw = kw.strip()
                if kw and kw.lower() in search_text:
                    excluded = True
                    break
            if excluded:
                continue
        if include_kw:
            matched = False
            for kw in include_kw.split(","):
                kw = kw.strip()
                if kw and kw.lower() in search_text:
                    matched = True
                    break
            if not matched and include_kw.strip():
                continue

        raw_item = RawItem(
            source_id=source.id,
            title=title,
            url=url,
            author=item.get("author", ""),
            summary=item.get("summary", ""),
            content=item.get("content", ""),
            published_at=item.get("published_at"),
            fetched_at=datetime.utcnow(),
            url_hash=url_hash,
            title_hash=title_hash,
            content_hash=sha256_hash(item.get("content", "")) if item.get("content") else None,
            status="pending",
            extra_data=item.get("extra_data"),
        )
        db.add(raw_item)
        new_count += 1

    log.new_count = new_count
    log.status = "success" if not error else "partial"
    if error:
        log.error_message = error
    log.finished_at = datetime.utcnow()
    db.commit()
    return log


def fetch_all_sources(db: Session) -> dict:
    """采集所有启用的信源"""
    sources = db.query(Source).filter(Source.enabled == True).all()
    results = {"total": len(sources), "success": 0, "failed": 0, "new_items": 0}
    for source in sources:
        try:
            log = fetch_source(db, source)
            if log.status == "failed":
                results["failed"] += 1
            else:
                results["success"] += 1
            results["new_items"] += log.new_count
        except Exception as e:
            results["failed"] += 1
    return results
