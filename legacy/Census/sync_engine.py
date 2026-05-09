#!/usr/bin/env python3
"""
CENSUS Sync Engine
================

The core synchronization engine for CENSUS system.
Handles incremental sync, garbage collection, and data consistency.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncpg
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SyncMetrics:
    """Metrics for sync operations."""
    total_records: int = 0
    processed_records: int = 0
    updated_records: int = 0
    deleted_records: int = 0
    errors: int = 0
    start_time: datetime = None
    end_time: Optional[datetime] = None

class SyncEngine:
    """
    The Sync Engine - Core of CENSUS synchronization.
    
    Features:
    - Incremental sync (last 24 hours)
    - Garbage collection (soft delete)
    - Resilience with retries
    - Performance optimization
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
        self.metrics = SyncMetrics()
    
    async def initialize(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Sync Engine initialized successfully")
            await self._create_indexes()
        except Exception as e:
            logger.error(f"Failed to initialize Sync Engine: {e}")
            raise
    
    async def _create_indexes(self):
        """Create performance indexes for common queries."""
        async with self.pool.acquire() as conn:
            # Index for device lookups by MAC
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_devices_mac 
                ON devices(mac_address)
            """)
            
            # Index for user lookups
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_userid 
                ON users(userid)
            """)
            
            # Index for line lookups
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lines_dn 
                ON telephony_lines(directory_number)
            """)
            
            # Composite index for device-user relationships
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_devices_user_status 
                ON devices(user_id, status)
            """)
            
            logger.info("Database indexes created/verified")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def run_incremental_sync(self, source_system: str = "cucm") -> SyncMetrics:
        """
        Run incremental sync for the last 24 hours.
        
        Args:
            source_system: Source system name (cucm, uccx, etc.)
        
        Returns:
            SyncMetrics with operation results
        """
        logger.info(f"Starting incremental sync from {source_system}")
        self.metrics = SyncMetrics(start_time=datetime.utcnow())
        
        try:
            async with self.pool.acquire() as conn:
                # Get cutoff time (24 hours ago)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Mark old inactive devices as soft deleted
                await self._garbage_collection(conn, cutoff_time)
                
                # Process incremental updates
                await self._process_incremental_updates(conn, source_system, cutoff_time)
                
                # Update sync metadata
                await self._update_sync_metadata(conn, source_system)
                
        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Sync failed: {e}")
            raise
        
        self.metrics.end_time = datetime.utcnow()
        return self.metrics
    
    async def _garbage_collection(self, conn, cutoff_time: datetime):
        """
        Garbage collection - mark old inactive devices as soft deleted.
        
        Devices inactive for more than 24 hours are marked as 'inactive'
        rather than hard deleted to maintain audit trail.
        """
        try:
            # Mark devices as inactive if not seen in 24 hours
            result = await conn.execute("""
                UPDATE devices 
                SET status = 'inactive',
                    updated_at = CURRENT_TIMESTAMP
                WHERE status = 'active' 
                  AND last_seen < $1
            """, cutoff_time)
            
            inactive_count = result.split()[-1:][0] if result else "0"
            logger.info(f"Marked {inactive_count} devices as inactive")
            
            self.metrics.deleted_records = int(inactive_count)
            
        except Exception as e:
            logger.error(f"Garbage collection failed: {e}")
            raise
    
    async def _process_incremental_updates(self, conn, source_system: str, cutoff_time: datetime):
        """
        Process incremental updates from source system.
        
        In production, this would:
        1. Query source system for changes since cutoff_time
        2. Transform and validate data
        3. Upsert to CENSUS database
        4. Handle conflicts and duplicates
        """
        try:
            # Simulate incremental sync - in production this would query actual source
            # For demo, we'll process some sample data
            
            # Get devices that need updates
            devices_to_update = await conn.fetch("""
                SELECT mac_address, device_name, device_type, model, status
                FROM devices 
                WHERE updated_at > $1 
                  OR last_seen > $1
                LIMIT 10000
            """, cutoff_time)
            
            self.metrics.total_records = len(devices_to_update)
            
            # Process each device (simulating source data updates)
            for device in devices_to_update:
                try:
                    # Simulate update from source system
                    updated_device = self._simulate_source_update(device, source_system)
                    
                    # Upsert to database
                    await conn.execute("""
                        INSERT INTO devices (
                            mac_address, device_name, device_type, model, 
                            status, updated_at, last_seen
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6
                        )
                        ON CONFLICT (mac_address) DO UPDATE SET
                            device_name = EXCLUDED.device_name,
                            device_type = EXCLUDED.device_type,
                            model = EXCLUDED.model,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at,
                            last_seen = EXCLUDED.last_seen
                    """, 
                    updated_device['mac_address'],
                    updated_device['device_name'],
                    updated_device['device_type'],
                    updated_device['model'],
                    updated_device['status'],
                    datetime.utcnow(),
                    updated_device['last_seen']
                    )
                    
                    self.metrics.processed_records += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process device {device['mac_address']}: {e}")
                    self.metrics.errors += 1
            
            logger.info(f"Processed {self.metrics.processed_records} device updates")
            
        except Exception as e:
            logger.error(f"Incremental update processing failed: {e}")
            raise
    
    def _simulate_source_update(self, device: Dict, source_system: str) -> Dict:
        """
        Simulate receiving an update from source system.
        
        In production, this would be actual data from CUCM/UCCX APIs.
        For demo, we simulate status changes.
        """
        import random
        
        # Simulate some devices becoming active/inactive
        if random.random() < 0.1:  # 10% chance of status change
            device['status'] = 'inactive' if device['status'] == 'active' else 'active'
            device['last_seen'] = datetime.utcnow()
        
        # Simulate some device metadata updates
        if random.random() < 0.05:  # 5% chance of metadata change
            device['device_name'] = f"{device['device_name']} (Updated)"
            device['updated_at'] = datetime.utcnow()
        
        return device
    
    async def _update_sync_metadata(self, conn, source_system: str):
        """Update sync metadata for tracking."""
        try:
            await conn.execute("""
                INSERT INTO sync_metadata (
                    source_system, last_sync_time, records_processed, 
                    records_updated, records_deleted, sync_status
                ) VALUES (
                    $1, $2, $3, $4, $5, 'completed'
                )
                ON CONFLICT (source_system) DO UPDATE SET
                    last_sync_time = EXCLUDED.last_sync_time,
                    records_processed = EXCLUDED.records_processed,
                    records_updated = EXCLUDED.records_updated,
                    records_deleted = EXCLUDED.records_deleted,
                    sync_status = EXCLUDED.sync_status,
                    updated_at = CURRENT_TIMESTAMP
            """,
            source_system,
            self.metrics.end_time or datetime.utcnow(),
            self.metrics.total_records,
            self.metrics.processed_records,
            self.metrics.deleted_records,
            self.metrics.errors
            )
            
        except Exception as e:
            logger.error(f"Failed to update sync metadata: {e}")
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and metrics."""
        try:
            async with self.pool.acquire() as conn:
                # Get recent sync history
                sync_history = await conn.fetch("""
                    SELECT source_system, last_sync_time, records_processed,
                           records_updated, records_deleted, sync_status
                    FROM sync_metadata 
                    ORDER BY last_sync_time DESC 
                    LIMIT 10
                """)
                
                # Get database statistics
                db_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_devices,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_devices,
                        COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_devices
                    FROM devices
                """)
                
                return {
                    "sync_history": [dict(row) for row in sync_history],
                    "database_stats": dict(db_stats) if db_stats else {},
                    "last_update": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Sync Engine shutdown")

# Global sync engine instance
sync_engine = None

async def get_sync_engine() -> SyncEngine:
    """Get or create sync engine instance."""
    global sync_engine
    if sync_engine is None:
        db_url = os.getenv("CENSUS_DB_URL", "postgresql://census_user:census_password@localhost:5432/census_db")
        sync_engine = SyncEngine(db_url)
        await sync_engine.initialize()
    return sync_engine

if __name__ == "__main__":
    async def main():
        """Test the sync engine."""
        engine = await get_sync_engine()
        
        try:
            # Run incremental sync
            metrics = await engine.run_incremental_sync("cucm")
            
            # Print results
            logger.info(f"Sync completed: {metrics}")
            
            # Get status
            status = await engine.get_sync_status()
            logger.info(f"Current status: {status}")
            
        finally:
            await engine.close()
    
    asyncio.run(main())
