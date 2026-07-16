"""Background job scheduler for market scans"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


# Timezone for the morning-briefing job. Stefan reads the dashboard in Sweden,
# so 14:00 here means 14:00 Swedish local time.
BRIEFING_TZ = "Europe/Stockholm"


def run_market_scan():
    """Execute a full market scan (data collection + screening)"""
    try:
        from app.pipeline import run_market_scan as pipeline_scan
        result = pipeline_scan()
        logger.info(f"Scan completed: {result['summary']}")
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}", exc_info=True)


def run_morning_briefing():
    """Generate and store the morning briefing (overnight job)."""
    from app.db import SessionLocal
    from app.routers.briefing import generate_and_store_briefing

    db = SessionLocal()
    try:
        b = generate_and_store_briefing(db)
        logger.info(f"Morning briefing generated for {b.date} ({b.usage_tokens} tokens)")
    except Exception as e:
        logger.error(f"Morning briefing failed: {str(e)}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler background job"""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return

    logger.info("Starting scheduler...")

    if settings.DEBUG:
        # DEV MODE: Every minute for testing
        scheduler.add_job(
            run_market_scan,
            CronTrigger(minute="*"),  # Every minute
            id="market_scan",
            name="Scheduled market scan (DEV - every minute)",
            replace_existing=True
        )
        logger.info("Scheduler started - DEV MODE: scans every minute")
    else:
        # PROD MODE: 5 minutes during pre-market hours
        # Cron: minute hour day month day_of_week
        # 0-59/5 4-9 * * 1-5 = every 5 minutes from 04:00-09:30, Mon-Fri
        scheduler.add_job(
            run_market_scan,
            CronTrigger(minute="0-59/5", hour="4-9", day_of_week="mon-fri"),
            id="market_scan",
            name="Scheduled market scan",
            replace_existing=True
        )
        logger.info("Scheduler started - PROD MODE: scans every 5 minutes during pre-market hours (04:00-09:30 EST, Mon-Fri)")

    # Morning briefing at 14:00 Swedish time, Mon-Fri.
    scheduler.add_job(
        run_morning_briefing,
        CronTrigger(hour=14, minute=0, day_of_week="mon-fri", timezone=BRIEFING_TZ),
        id="morning_briefing",
        name="Morning briefing (14:00 Europe/Stockholm, Mon-Fri)",
        replace_existing=True,
    )
    logger.info("Morning briefing job scheduled - 14:00 Europe/Stockholm, Mon-Fri")

    # Start the scheduler thread so the jobs added above actually fire.
    scheduler.start()
    logger.info("Scheduler thread started")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def trigger_scan_now():
    """Manually trigger a scan immediately"""
    logger.info("Manual scan triggered")
    run_market_scan()


def trigger_briefing_now():
    """Manually trigger the morning briefing immediately (for testing)."""
    logger.info("Manual morning briefing triggered")
    run_morning_briefing()


def get_next_run():
    """Get the next scheduled run time"""
    try:
        job = scheduler.get_job("market_scan")
        if job:
            # APScheduler 3.x uses next_run_time
            if hasattr(job, 'next_run_time'):
                return job.next_run_time
    except Exception as e:
        logger.warning(f"Could not get next run time: {e}")
    return None
