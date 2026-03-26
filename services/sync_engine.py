"""
Synchronization Engine - Core orchestration for CENSUS data synchronization.
Coordinates data from CUCM (via AXLerate) and Phone Scraper into PostgreSQL.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
import uuid

from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    User, Device, SwitchConnection, SyncLog, 
    Line, DeviceLineAssociation
)
from services.axlerate_client import AXLerateClient
from services.phone_scraper import scan_phones_network
from core.config import get_settings


logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Core synchronization engine for CENSUS MVP.
    Orchestrates data collection from CUCM and network topology.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize sync engine with database session."""
        self.db = db
        self.sync_start_time = datetime.utcnow()
        self.settings = get_settings()
    
    async def run_full_sync(self) -> Dict:
        """
        Run complete synchronization pipeline.
        
        Returns:
            Dictionary with sync statistics and results
        """
        logger.info("🚀 Starting CENSUS MVP synchronization")
        sync_stats = {
            "users_synced": 0,
            "devices_synced": 0,
            "switches_synced": 0,
            "switch_connections_synced": 0,
            "errors": [],
            "start_time": self.sync_start_time
        }
        
        try:
            # Step A: Sync Users from CUCM
            logger.info("📋 Step A: Syncing Users from CUCM")
            user_stats = await self._sync_cucm_users()
            sync_stats.update(user_stats)
            
            # Step B: Fetch Devices from CUCM
            logger.info("📱 Step B: Fetching Devices from CUCM via AXLerate")
            cucm_devices = await self._fetch_cucm_devices()
            sync_stats["cucm_devices_fetched"] = len(cucm_devices)
            
            # Step C: Scrape Local Network Topology
            logger.info("🔌 Step C: Scraping Network Topology from Local Phones")
            cdp_data = await self._scrape_network_topology(cucm_devices)
            sync_stats["cdp_data_found"] = len(cdp_data)
            
            # Step D: Sync Switches & Endpoints
            logger.info("🌐 Step D: Syncing Switches and Endpoints")
            device_stats = await self._sync_switches_and_endpoints(cucm_devices, cdp_data, sync_stats.get("user_lookup", {}))
            sync_stats.update(device_stats)
            
            # Log successful sync
            await self._log_sync_result("full", "success", sync_stats)
            await self.db.commit()
            
            logger.info("✅ Full synchronization completed successfully")
            return sync_stats
            
        except Exception as e:
            logger.error(f"❌ Full synchronization failed: {e}")
            sync_stats["errors"].append(str(e))
            await self._log_sync_result("full", "failed", sync_stats)
            await self.db.rollback()
            raise
    
    async def _sync_cucm_users(self) -> Dict:
        """Sync users from CUCM via AXLerate."""
        try:
            axl_client = AXLerateClient()
            users_data = await axl_client.fetch_cucm_users()
            
            if not users_data:
                logger.warning("No users returned from CUCM")
                return {"users_synced": 0}
            
            # Transform CUCM data to database format
            db_users = []
            for user in users_data:
                db_user = {
                    "sam_account_name": user["ad_username"],
                    "display_name": user["full_name"],
                    "department": user["department"],
                    "is_active": user["is_active"],
                    "last_ad_sync": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                db_users.append(db_user)
            
            # UPSERT users
            stmt = insert(User).values(db_users)
            stmt = stmt.on_conflict_do_update(
                index_elements=['sam_account_name'],
                set_=dict(
                    display_name=stmt.excluded.display_name,
                    department=stmt.excluded.department,
                    is_active=stmt.excluded.is_active,
                    last_ad_sync=stmt.excluded.last_ad_sync,
                    updated_at=stmt.excluded.updated_at
                )
            )
            
            await self.db.execute(stmt)
            logger.info(f"✅ Synced {len(users_data)} users from CUCM")
            
            # Create user lookup dictionary for device linking
            user_lookup = await self._create_user_lookup(users_data)
            
            return {"users_synced": len(users_data), "user_lookup": user_lookup}
            
        except Exception as e:
            logger.error(f"❌ Failed to sync CUCM users: {e}")
            raise
    
    async def _create_user_lookup(self, users_data: List[Dict]) -> Dict[str, uuid.UUID]:
        """Create lookup dictionary mapping username to user ID."""
        try:
            # Get all user IDs from database
            result = await self.db.execute(
                select(User.sam_account_name, User.id).where(
                    User.sam_account_name.in_([user["ad_username"] for user in users_data])
                )
            )
            
            user_lookup = {username: user_id for username, user_id in result.all()}
            logger.info(f"✅ Created user lookup for {len(user_lookup)} users")
            return user_lookup
            
        except Exception as e:
            logger.error(f"❌ Failed to create user lookup: {e}")
            raise
    
    async def _fetch_cucm_devices(self) -> List[Dict]:
        """Fetch devices from CUCM via AXLerate."""
        try:
            axl_client = AXLerateClient()
            devices = await axl_client.fetch_registered_endpoints()
            
            logger.info(f"✅ Fetched {len(devices)} devices from CUCM")
            return devices
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch CUCM devices: {e}")
            raise
    
    async def _scrape_network_topology(self, cucm_devices: List[Dict]) -> Dict:
        """Scrape CDP data from phones in local subnets only."""
        try:
            # Extract valid IP addresses from local subnet only
            ip_list = [
                device["ip_address"] 
                for device in cucm_devices 
                if (device.get("ip_address") and 
                    device["is_registered"] and 
                    device["ip_address"].startswith(self.settings.LOCAL_SUBNET_PREFIX))
            ]
            
            if not ip_list:
                logger.warning(f"No registered devices found in local subnet {self.settings.LOCAL_SUBNET_PREFIX}")
                return {}
            
            logger.info(f"Scanning {len(ip_list)} devices in local subnet {self.settings.LOCAL_SUBNET_PREFIX}")
            
            # Scrape network topology
            cdp_results = await scan_phones_network(ip_list)
            
            # Create fast lookup dictionary
            cdp_lookup = {
                result["ip_address"]: {
                    "switch_name": result["switch_name"],
                    "switch_port": result["switch_port"]
                }
                for result in cdp_results
            }
            
            logger.info(f"✅ Scraped CDP data for {len(cdp_results)} phones")
            return cdp_lookup
            
        except Exception as e:
            logger.error(f"❌ Failed to scrape network topology: {e}")
            raise
    
    async def _sync_switches_and_endpoints(self, cucm_devices: List[Dict], 
                                       cdp_lookup: Dict, user_lookup: Dict) -> Dict:
        """Sync switches and endpoints with topology data."""
        try:
            devices_synced = 0
            devices_with_topology = 0
            switches_synced = 0
            
            # Extract unique switches from CDP data
            unique_switches = set()
            for cdp_info in cdp_lookup.values():
                if cdp_info["switch_name"]:
                    unique_switches.add(cdp_info["switch_name"])
            
            # Upsert switches (we'll store minimal switch info)
            switch_records = []
            for switch_name in unique_switches:
                switch_records.append({
                    "name": switch_name,
                    "ip_address": None,  # Could be resolved in future
                    "model": None,
                    "location": None,
                    "updated_at": datetime.utcnow()
                })
            
            if switch_records:
                # Note: We don't have a network_switches table in current schema
                # Switch info is stored directly in SwitchConnection
                logger.info(f"✅ Found {len(unique_switches)} unique switches")
                switches_synced = len(unique_switches)
            
            # Process devices
            for device_data in cucm_devices:
                # Get topology data for this device
                ip_address = device_data.get("ip_address")
                topology_data = cdp_lookup.get(ip_address, {}) if ip_address else {}
                
                # Get user ID from lookup
                owner_username = device_data.get("owner_username")
                user_id = user_lookup.get(owner_username) if owner_username else None
                
                # Prepare device record
                db_device = {
                    "name": device_data["name"],
                    "description": device_data.get("description"),
                    "device_type": device_data.get("device_type"),
                    "model": device_data.get("model"),
                    "ip_address": ip_address,
                    "mac_address": device_data.get("mac_address"),
                    "status": device_data.get("status", "unknown"),
                    "owner_user_id": user_id,
                    "last_seen_from_cucm": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # UPSERT device
                stmt = insert(Device).values(db_device)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['name'],
                    set_=dict(
                        description=stmt.excluded.description,
                        device_type=stmt.excluded.device_type,
                        model=stmt.excluded.model,
                        ip_address=stmt.excluded.ip_address,
                        mac_address=stmt.excluded.mac_address,
                        status=stmt.excluded.status,
                        owner_user_id=stmt.excluded.owner_user_id,
                        last_seen_from_cucm=stmt.excluded.last_seen_from_cucm,
                        updated_at=stmt.excluded.updated_at
                    )
                )
                
                await self.db.execute(stmt)
                devices_synced += 1
                
                # Create switch connection if topology data exists
                if topology_data and topology_data.get("switch_name"):
                    await self._create_switch_connection(
                        device_data["name"],
                        topology_data
                    )
                    devices_with_topology += 1
            
            logger.info(f"✅ Synced {devices_synced} devices, {devices_with_topology} with topology")
            
            return {
                "devices_synced": devices_synced,
                "devices_with_topology": devices_with_topology,
                "switches_synced": switches_synced
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to sync switches and endpoints: {e}")
            raise
    
    async def _create_switch_connection(self, device_name: str, 
                                     topology_data: Dict) -> None:
        """Create or update switch connection for a device."""
        try:
            # Get device ID
            device_result = await self.db.execute(
                select(Device.id).where(Device.name == device_name)
            )
            device_id = device_result.scalar_one_or_none()
            
            if not device_id:
                logger.warning(f"Device not found for switch connection: {device_name}")
                return
            
            # Delete existing switch connections for this device
            await self.db.execute(
                delete(SwitchConnection).where(SwitchConnection.device_id == device_id)
            )
            
            # Create new switch connection
            switch_connection = {
                "device_id": device_id,
                "switch_name": topology_data["switch_name"],
                "switch_ip": None,  # Could be extracted from switch name in future
                "switch_model": None,
                "local_port": None,
                "remote_port": topology_data.get("switch_port"),
                "port_description": None,
                "vlan": None,
                "discovery_protocol": "CDP",
                "last_seen": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db.execute(insert(SwitchConnection).values(switch_connection))
            
        except Exception as e:
            logger.error(f"❌ Failed to create switch connection for {device_name}: {e}")
            raise
    
    async def _log_sync_result(self, sync_type: str, status: str, 
                             stats: Dict) -> None:
        """Log synchronization result to database."""
        try:
            sync_log = {
                "sync_type": sync_type,
                "source": "sync_engine_mvp",
                "status": status,
                "records_processed": stats.get("users_synced", 0) + stats.get("devices_synced", 0),
                "records_created": stats.get("users_synced", 0) + stats.get("devices_synced", 0),
                "records_updated": 0,
                "records_failed": len(stats.get("errors", [])),
                "records_orphaned": 0,
                "started_at": self.sync_start_time,
                "completed_at": datetime.utcnow(),
                "duration_seconds": (datetime.utcnow() - self.sync_start_time).total_seconds(),
                "error_message": "; ".join(stats.get("errors", [])) if stats.get("errors") else None,
                "details": stats
            }
            
            await self.db.execute(insert(SyncLog).values(sync_log))
            
        except Exception as e:
            logger.error(f"❌ Failed to log sync result: {e}")


# Main sync function for external usage
async def run_full_sync(db: AsyncSession) -> Dict:
    """
    Run full synchronization pipeline.
    
    Args:
        db: Async database session
        
    Returns:
        Dictionary with sync statistics
    """
    engine = SyncEngine(db)
    return await engine.run_full_sync()


# Convenience functions for individual sync steps
async def sync_users_only(db: AsyncSession) -> Dict:
    """Sync only users from CUCM."""
    engine = SyncEngine(db)
    return await engine._sync_cucm_users()


async def sync_devices_only(db: AsyncSession) -> Dict:
    """Sync only devices from CUCM."""
    engine = SyncEngine(db)
    devices = await engine._fetch_cucm_devices()
    cdp_data = await engine._scrape_network_topology(devices)
    user_lookup = {}  # Would need to call user sync first
    return await engine._sync_switches_and_endpoints(devices, cdp_data, user_lookup)


# Example usage
if __name__ == "__main__":
    import asyncio
    from database.session import AsyncSessionLocal
    
    async def main():
        """Test sync engine."""
        async with AsyncSessionLocal() as db:
            try:
                stats = await run_full_sync(db)
                
                print("🎉 Sync completed successfully!")
                print(f"Users synced: {stats.get('users_synced', 0)}")
                print(f"Devices synced: {stats.get('devices_synced', 0)}")
                print(f"Switch connections: {stats.get('switch_connections_synced', 0)}")
                
            except Exception as e:
                print(f"❌ Sync failed: {e}")
    
    # Run test
    asyncio.run(main())
