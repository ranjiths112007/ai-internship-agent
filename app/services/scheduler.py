from __future__ import annotations

import logging
import threading
import time
from typing import Optional
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.discovery import run_discovery_pipeline

logger = logging.getLogger(__name__)

_scheduler_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def _run_scheduled_discovery_task():
    logger.info("Scheduler thread started.")
    interval_seconds = max(3600, settings.discovery_interval_hours * 3600)
    while not _stop_event.is_set():
        try:
            logger.info("Executing scheduled discovery run...")
            with SessionLocal() as db:
                res = run_discovery_pipeline(db)
                logger.info(f"Scheduled discovery finished: {res.new_jobs} new jobs, {res.high_fit_jobs} high-fit.")
        except Exception as e:
            logger.error(f"Error in scheduled discovery: {e}")

        # Sleep in chunks to allow quick shutdown
        for _ in range(int(interval_seconds // 5)):
            if _stop_event.is_set():
                break
            time.sleep(5)


def start_discovery_scheduler():
    global _scheduler_thread
    if not settings.discovery_enabled:
        logger.info("Discovery scheduler is disabled via DISCOVERY_ENABLED setting.")
        return

    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.info("Discovery scheduler thread is already running.")
        return

    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_run_scheduled_discovery_task, daemon=True)
    _scheduler_thread.start()
    logger.info(f"Discovery scheduler started. Running every {settings.discovery_interval_hours} hours.")


def stop_discovery_scheduler():
    global _scheduler_thread
    _stop_event.set()
    if _scheduler_thread:
        _scheduler_thread.join(timeout=2.0)
        _scheduler_thread = None
        logger.info("Discovery scheduler stopped.")
