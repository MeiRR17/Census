#!/usr/bin/env python3
"""
Phone Scraper - Incremental Device Discovery
==========================================

Incrementally scrapes phone data from CUCM/UCCX systems.
Handles real-time device discovery with change detection.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    """Device information from Cisco systems."""
    mac_address: str
    device_name: str
    device_type: str
    model: str
    status: str = "active"
    ip_address: Optional[str] = None
    last_seen: datetime = None
    site_id: Optional[str] = None
    description: Optional[str] = None

class PhoneScraper:
    """
    Incremental phone scraper for Cisco UC systems.
    
    Features:
    - Real-time device discovery
    - Change detection and alerts
    - Incremental updates only
    - Resilient connection handling
    """
    
    def __init__(self, cucm_url: str, username: str, password: str):
        self.cucm_url = cucm_url
        self.username = username
        self.password = password
        self.session = None
        self.last_sync_time = None
        self.discovered_devices: Set[str] = set()
    
    async def initialize(self):
        """Initialize HTTP session and get last sync time."""
        self.session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.username, self.password),
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Get last sync time from database (in production)
        # For demo, we'll use a recent timestamp
        self.last_sync_time = datetime.utcnow() - timedelta(hours=1)
        logger.info(f"Phone scraper initialized, last sync: {self.last_sync_time}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def discover_devices(self) -> List[DeviceInfo]:
        """
        Discover devices from CUCM/UCCX systems.
        
        Returns:
            List of discovered devices
        """
        logger.info("Starting device discovery")
        devices = []
        
        try:
            # In production, this would query actual CUCM/UCCX APIs
            # For demo, we'll simulate device discovery
            
            # Simulate discovering different device types
            device_types = ["Cisco 8841", "Cisco 8851", "Cisco 7841", "Cisco 8861"]
            
            for i in range(50):  # Simulate 50 devices
                import random
                
                # Generate realistic MAC address
                mac = f"SEP{random.randint(100000000000, 999999999999):012X}"
                
                # Create device info
                device = DeviceInfo(
                    mac_address=mac,
                    device_name=f"PHONE-{i:03d}",
                    device_type=random.choice(device_types),
                    model=random.choice(device_types),
                    status=random.choice(["active", "inactive", "registering"]),
                    ip_address=f"192.168.1.{random.randint(100, 200)}",
                    last_seen=datetime.utcnow() - timedelta(minutes=random.randint(0, 1440)),
                    site_id=f"SITE-{random.randint(1, 5)}",
                    description=f"Phone in {random.choice(['Main Office', 'Branch A', 'Branch B'])}"
                )
                
                devices.append(device)
                self.discovered_devices.add(mac)
            
            logger.info(f"Discovered {len(devices)} devices")
            return devices
            
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
            raise
    
    async def detect_changes(self, new_devices: List[DeviceInfo]) -> Dict[str, List[DeviceInfo]]:
        """
        Detect changes between current and previous discovery.
        
        Returns:
            Dictionary with change categories: 'new', 'updated', 'unchanged'
        """
        changes = {
            'new': [],
            'updated': [],
            'unchanged': []
        }
        
        for device in new_devices:
            if device.mac_address not in self.discovered_devices:
                # New device discovered
                changes['new'].append(device)
                logger.info(f"New device discovered: {device.mac_address}")
            else:
                # Existing device - check if changed
                changes['unchanged'].append(device)
        
        # Update discovered devices set
        self.discovered_devices = {device.mac_address: device for device in new_devices}
        
        return changes
    
    async def get_device_details(self, mac_address: str) -> Optional[DeviceInfo]:
        """
        Get detailed information for a specific device.
        """
        try:
            # In production, this would query CUCM/UCCX for device details
            # For demo, return from discovered devices
            return self.discovered_devices.get(mac_address)
            
        except Exception as e:
            logger.error(f"Failed to get device details for {mac_address}: {e}")
            return None
    
    async def monitor_device_status(self, mac_address: str) -> Dict[str, Any]:
        """
        Monitor real-time status of a specific device.
        """
        try:
            # Simulate real-time status monitoring
            import random
            
            device = self.discovered_devices.get(mac_address)
            if not device:
                return {"error": "Device not found"}
            
            # Simulate status changes
            if random.random() < 0.1:  # 10% chance of status change
                device.status = random.choice(["active", "inactive", "registering", "unreachable"])
                device.last_seen = datetime.utcnow()
            
            return {
                "mac_address": mac_address,
                "status": device.status,
                "last_seen": device.last_seen.isoformat(),
                "ip_address": device.ip_address,
                "response_time": random.uniform(10, 100)  # ms
            }
            
        except Exception as e:
            logger.error(f"Status monitoring failed for {mac_address}: {e}")
            return {"error": str(e)}
    
    async def get_active_devices_count(self) -> int:
        """Get count of currently active devices."""
        active_count = sum(
            1 for device in self.discovered_devices.values() 
            if device.status == "active"
        )
        return active_count
    
    async def get_devices_by_site(self, site_id: str) -> List[DeviceInfo]:
        """Get all devices for a specific site."""
        return [
            device for device in self.discovered_devices.values()
            if device.site_id == site_id
        ]
    
    async def get_devices_by_type(self, device_type: str) -> List[DeviceInfo]:
        """Get all devices of a specific type."""
        return [
            device for device in self.discovered_devices.values()
            if device_type in device.device_type
        ]
    
    async def export_devices(self, format: str = "json") -> str:
        """
        Export discovered devices in specified format.
        
        Args:
            format: Export format ('json', 'csv', 'xml')
        
        Returns:
            Exported data as string
        """
        devices_data = []
        
        for device in self.discovered_devices.values():
            device_dict = {
                "mac_address": device.mac_address,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "model": device.model,
                "status": device.status,
                "ip_address": device.ip_address,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "site_id": device.site_id,
                "description": device.description
            }
            devices_data.append(device_dict)
        
        if format.lower() == "json":
            import json
            return json.dumps(devices_data, indent=2, default=str)
        
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if devices_data:
                writer = csv.DictWriter(output, fieldnames=devices_data[0].keys())
                writer.writeheader()
                writer.writerows(devices_data)
            
            return output.getvalue()
        
        elif format.lower() == "xml":
            # Simple XML export
            xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
            xml_lines.append('<devices>')
            
            for device in devices_data:
                xml_lines.append('  <device>')
                for key, value in device.items():
                    if value is not None:
                        xml_lines.append(f'    <{key}>{value}</{key}>')
                xml_lines.append('  </device>')
            
            xml_lines.append('</devices>')
            return '\n'.join(xml_lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            logger.info("Phone scraper shutdown")

# Global scraper instance
phone_scraper = None

async def get_phone_scraper() -> PhoneScraper:
    """Get or create phone scraper instance."""
    global phone_scraper
    if phone_scraper is None:
        cucm_url = os.getenv("CUCM_URL", "https://cucm.company.com:8443")
        username = os.getenv("CUCM_USERNAME", "admin")
        password = os.getenv("CUCM_PASSWORD", "password")
        
        phone_scraper = PhoneScraper(cucm_url, username, password)
        await phone_scraper.initialize()
    
    return phone_scraper

if __name__ == "__main__":
    async def main():
        """Test the phone scraper."""
        scraper = await get_phone_scraper()
        
        try:
            # Discover devices
            devices = await scraper.discover_devices()
            print(f"Discovered {len(devices)} devices")
            
            # Detect changes
            changes = await scraper.detect_changes(devices)
            print(f"Changes: {len(changes['new'])} new, {len(changes['updated'])} updated")
            
            # Get device details
            if devices:
                sample_device = await scraper.get_device_details(devices[0].mac_address)
                print(f"Sample device: {sample_device}")
            
            # Monitor status
            status = await scraper.monitor_device_status(devices[0].mac_address)
            print(f"Device status: {status}")
            
            # Export data
            json_export = await scraper.export_devices("json")
            print(f"JSON export preview: {json_export[:200]}...")
            
        finally:
            await scraper.close()
    
    asyncio.run(main())
