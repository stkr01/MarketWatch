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
    # TODO: Implement full scan pipeline
    print(f"[{datetime.utcnow().isoformat()}] Market scan started")
    logger.info("Market scan started")


def start_scheduler():
    """Start the APScheduler background job"""
    if scheduler.running:
        return

    # Schedule scan every 5 minutes during pre-market hours
    # Cron: minute hour day month day_of_week
    # 0-30/5 4-9 * * 1-5 = every 5 minutes from 04:00-09:30, Mon-Fri
    scheduler.add_job(
        run_market_scan,
        CronTrigger(minute="0-59/5", hour="4-9", day_of_week="mon-fri"),
        id="market_scan",
        name="Scheduled market scan",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def trigger_scan_now():
    """Manually trigger a scan immediately"""
    run_market_scan()
