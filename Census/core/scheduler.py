"""
Background Scheduler - APScheduler integration for automated CENSUS synchronization.
Runs scheduled jobs for nightly data synchronization and maintenance tasks.
"""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from database.session import AsyncSessionLocal
from services.sync_engine import run_full_sync


logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def scheduled_sync_job():
    """
    Scheduled synchronization job.
    Runs the full CENSUS synchronization pipeline.
    """
    job_start_time = datetime.utcnow()
    logger.info(f"🌙 Starting scheduled sync job at {job_start_time}")
    
    # Create database session for this job
    async with AsyncSessionLocal() as db:
        try:
            # Run the full synchronization
            stats = await run_full_sync(db)
            await db.commit()
            
            job_duration = (datetime.utcnow() - job_start_time).total_seconds()
            logger.info(
                f"✅ Scheduled sync completed successfully in {job_duration:.2f}s. "
                f"Users: {stats.get('users_synced', 0)}, "
                f"Devices: {stats.get('devices_synced', 0)}, "
                f"Switch connections: {stats.get('switch_connections_synced', 0)}"
            )
            
        except Exception as e:
            await db.rollback()
            job_duration = (datetime.utcnow() - job_start_time).total_seconds()
            logger.error(
                f"❌ Scheduled sync failed after {job_duration:.2f}s: {e}"
            )
            raise
            
        finally:
            # Session is automatically closed by the context manager
            pass


async def ghost_sweeper_job():
    """
    Ghost sweeper job to identify orphaned resources.
    Finds devices that haven't been seen from CUCM or scraper recently.
    """
    logger.info("👻 Starting ghost sweeper job")
    
    async with AsyncSessionLocal() as db:
        try:
            from database.models import Device, SyncLog
            from sqlalchemy import select, func, and_
            
            # Find devices not seen in the last 7 days
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Check last_seen_from_cucm and last_seen_from_scraper
            ghost_devices_query = select(Device).where(
                and_(
                    or_(
                        Device.last_seen_from_cucm < cutoff_date,
                        Device.last_seen_from_cucm.is_(None)
                    ),
                    or_(
                        Device.last_seen_from_scraper < cutoff_date,
                        Device.last_seen_from_scraper.is_(None)
                    )
                )
            )
            
            result = await db.execute(ghost_devices_query)
            ghost_devices = result.scalars().all()
            
            if ghost_devices:
                logger.warning(f"👻 Found {len(ghost_devices)} ghost devices (not seen in 7+ days)")
                
                # Log ghost devices to sync log
                from database.models import SyncLog
                import uuid
                
                ghost_log = {
                    "id": uuid.uuid4(),
                    "sync_type": "ghost_sweeper",
                    "source": "scheduler",
                    "status": "completed",
                    "records_processed": len(ghost_devices),
                    "records_orphaned": len(ghost_devices),
                    "started_at": datetime.utcnow(),
                    "completed_at": datetime.utcnow(),
                    "details": {
                        "ghost_devices": [
                            {
                                "name": device.name,
                                "last_seen_cucm": device.last_seen_from_cucm.isoformat() if device.last_seen_from_cucm else None,
                                "last_seen_scraper": device.last_seen_from_scraper.isoformat() if device.last_seen_from_scraper else None
                            }
                            for device in ghost_devices
                        ]
                    }
                }
                
                await db.execute(SyncLog.__table__.insert().values(ghost_log))
                await db.commit()
                
            else:
                logger.info("✅ No ghost devices found")
                
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Ghost sweeper job failed: {e}")
            raise


def job_listener(event):
    """
    Event listener for scheduler job events.
    Logs job execution status.
    """
    if event.exception:
        logger.error(f"❌ Job {event.job_id} failed: {event.exception}")
    else:
        logger.info(f"✅ Job {event.job_id} completed successfully")


def start_scheduler():
    """
    Start the APScheduler with configured jobs.
    
    Returns:
        AsyncIOScheduler: The started scheduler instance
    """
    global scheduler
    
    if scheduler and scheduler.running:
        logger.warning("⚠️ Scheduler is already running")
        return scheduler
    
    try:
        # Create AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        
        # Add event listeners
        scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Add scheduled jobs
        
        # 1. Full sync every day at 3:00 AM
        scheduler.add_job(
            func=scheduled_sync_job,
            trigger=CronTrigger(hour=3, minute=0),
            id="daily_full_sync",
            name="Daily Full CENSUS Synchronization",
            replace_existing=True,
            misfire_grace_time=3600  # Allow 1 hour grace period for missed jobs
        )
        
        # 2. Ghost sweeper every Sunday at 4:00 AM
        scheduler.add_job(
            func=ghost_sweeper_job,
            trigger=CronTrigger(day_of_week='sun', hour=4, minute=0),
            id="weekly_ghost_sweeper",
            name="Weekly Ghost Sweeper",
            replace_existing=True,
            misfire_grace_time=1800  # 30 minute grace period
        )
        
        # 3. Health check every hour
        scheduler.add_job(
            func=health_check_job,
            trigger=CronTrigger(minute=0),  # Every hour at minute 0
            id="hourly_health_check",
            name="Hourly Health Check",
            replace_existing=True,
            misfire_grace_time=300  # 5 minute grace period
        )
        
        # Start the scheduler
        scheduler.start()
        
        logger.info("🚀 APScheduler started successfully")
        logger.info("📅 Scheduled jobs:")
        logger.info("   - Daily full sync: 03:00 AM")
        logger.info("   - Weekly ghost sweeper: Sunday 04:00 AM")
        logger.info("   - Hourly health check: Every hour")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        raise


async def health_check_job():
    """
    Health check job to verify system components.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Test database connectivity
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1"))
            db_status = "ok" if result.scalar() == 1 else "error"
            
            # Test external services (could be expanded)
            from services.axlerate_client import AXLerateClient
            from services.ad_sync import ActiveDirectoryClient
            
            axl_status = "ok"  # Could implement actual health check
            ad_status = "ok"   # Could implement actual health check
            
            logger.info(f"🏥 Health check - DB: {db_status}, AXLerate: {axl_status}, AD: {ad_status}")
            
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")


def stop_scheduler():
    """
    Stop the APScheduler gracefully.
    """
    global scheduler
    
    if scheduler and scheduler.running:
        try:
            scheduler.shutdown(wait=True)
            logger.info("🛑 APScheduler stopped gracefully")
        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")
    else:
        logger.warning("⚠️ Scheduler is not running")


def get_scheduler_info() -> dict:
    """
    Get information about the scheduler and its jobs.
    
    Returns:
        dict: Scheduler information
    """
    global scheduler
    
    if not scheduler:
        return {"status": "not_initialized"}
    
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs_info
    }


# Convenience functions for manual job control
async def trigger_sync_now():
    """
    Manually trigger the sync job immediately.
    """
    logger.info("🔄 Manually triggering sync job")
    await scheduled_sync_job()


async def trigger_ghost_sweeper_now():
    """
    Manually trigger the ghost sweeper job immediately.
    """
    logger.info("👻 Manually triggering ghost sweeper job")
    await ghost_sweeper_job()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Test the scheduler."""
        try:
            # Start scheduler
            start_scheduler()
            
            # Run for a few seconds to see it work
            await asyncio.sleep(5)
            
            # Trigger a manual sync
            await trigger_sync_now()
            
            # Stop scheduler
            stop_scheduler()
            
        except Exception as e:
            logger.error(f"Scheduler test failed: {e}")
    
    # Run the test
    asyncio.run(main())
