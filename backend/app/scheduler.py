"""Background job scheduler for market scans"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_market_scan():
    """Execute a full market scan (data collection + screening)"""
    try:
        from app.pipeline import run_market_scan as pipeline_scan
        result = pipeline_scan()
        logger.info(f"Scan completed: {result['summary']}")
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}", exc_info=True)


def start_scheduler():
    """Start the APScheduler background job"""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    logger.info("Starting scheduler...")

    # Schedule scan every 5 minutes during pre-market hours
    # Cron: minute hour day month day_of_week
    # 0-59/5 4-9 * * 1-5 = every 5 minutes from 04:00-09:30, Mon-Fri
    scheduler.add_job(
        run_market_scan,
        CronTrigger(minute="0-59/5", hour="4-9", day_of_week="mon-fri"),
        id="market_scan",
        name="Scheduled market scan",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started - scans every 5 minutes during pre-market hours (04:00-09:30 EST, Mon-Fri)")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def trigger_scan_now():
    """Manually trigger a scan immediately"""
    logger.info("Manual scan triggered")
    run_market_scan()


def get_next_run():
    """Get the next scheduled run time"""
    job = scheduler.get_job("market_scan")
    if job:
        return job.next_run_time
    return None
