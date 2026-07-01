"""任务调度服务：使用APScheduler实现每日定时任务"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScheduleConfig
from app.services.digest_service import run_full_pipeline, fetch_all_sources_only
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
_scheduler_started = False


def _get_schedule_config(db: Session) -> ScheduleConfig:
    config = db.query(ScheduleConfig).first()
    if not config:
        config = ScheduleConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def _fetch_job():
    """采集任务"""
    db = SessionLocal()
    try:
        logger.info("定时采集任务开始")
        fetch_all_sources_only(db)
        logger.info("定时采集任务完成")
    except Exception as e:
        logger.error(f"定时采集任务失败: {e}")
    finally:
        db.close()


def _digest_job():
    """生成日报任务"""
    db = SessionLocal()
    try:
        logger.info("定时生成日报任务开始")
        from app.services.digest_service import generate_digest
        generate_digest(db, job_type="daily")
        logger.info("定时生成日报任务完成")
    except Exception as e:
        logger.error(f"定时生成日报任务失败: {e}")
    finally:
        db.close()


def _send_job():
    """发送邮件任务"""
    db = SessionLocal()
    try:
        logger.info("定时发送邮件任务开始")
        from app.services.digest_service import send_latest_digest
        send_latest_digest(db)
        logger.info("定时发送邮件任务完成")
    except Exception as e:
        logger.error(f"定时发送邮件任务失败: {e}")
    finally:
        db.close()


def reload_schedule():
    """重新加载调度配置"""
    db = SessionLocal()
    try:
        config = _get_schedule_config(db)
        # 移除旧任务
        for job_id in ["daily_fetch", "daily_digest", "daily_send"]:
            try:
                scheduler.remove_job(job_id)
            except Exception:
                pass

        if not config.enabled:
            logger.info("调度任务已禁用")
            return

        # 解析时间
        fetch_h, fetch_m = map(int, config.fetch_time.split(":"))
        digest_h, digest_m = map(int, config.digest_time.split(":"))
        send_h, send_m = map(int, config.send_time.split(":"))

        # 工作日过滤
        day_of_week = "mon-fri" if config.weekdays_only else "*"

        scheduler.add_job(
            _fetch_job,
            CronTrigger(hour=fetch_h, minute=fetch_m, day_of_week=day_of_week, timezone=config.timezone),
            id="daily_fetch",
            replace_existing=True,
        )
        scheduler.add_job(
            _digest_job,
            CronTrigger(hour=digest_h, minute=digest_m, day_of_week=day_of_week, timezone=config.timezone),
            id="daily_digest",
            replace_existing=True,
        )
        scheduler.add_job(
            _send_job,
            CronTrigger(hour=send_h, minute=send_m, day_of_week=day_of_week, timezone=config.timezone),
            id="daily_send",
            replace_existing=True,
        )
        logger.info(f"调度任务已更新: 采集{config.fetch_time}, 生成{config.digest_time}, 发送{config.send_time}")
    finally:
        db.close()


def start_scheduler():
    """启动调度器"""
    global _scheduler_started
    if _scheduler_started:
        return
    if not scheduler.running:
        scheduler.start()
    _scheduler_started = True
    reload_schedule()
    logger.info("调度器已启动")


def shutdown_scheduler():
    """关闭调度器"""
    global _scheduler_started
    if scheduler.running:
        scheduler.shutdown(wait=False)
    _scheduler_started = False
