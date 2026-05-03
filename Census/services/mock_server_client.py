"""
Mock Server Client - HTTP client for Cisco mock server integration.
Acts as an async HTTP client to the mock Cisco server for CUCM and CMS data.
"""

import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from core.config import get_settings


logger = logging.getLogger(__name__)


class CUCMDevice(BaseModel):
    """Pydantic model for CUCM device information from mock server."""
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    owner_username: Optional[str] = None


class CUCMUser(BaseModel):
    """Pydantic model for CUCM user information from mock server."""
    userid: str
    firstname: str
    lastname: str
    department: Optional[str] = None
    status: int


class MockServerClient:
    """
    Async HTTP client for Mock Cisco Server.
    Provides methods to fetch device and user information from the mock server.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the mock server client.
        
        Args:
            base_url: Base URL of the mock server. If None, uses config.
        """
        self.settings = get_settings()
        self.base_url = base_url or "http://telephony-mock-server:8001"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Content-Type": "application/json"}
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _make_request(self, endpoint: str) -> Dict:
        """
        Make an HTTP GET request to mock server.
        
        Args:
            endpoint: API endpoint to call
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        url = urljoin(self.base_url, endpoint)
        logger.info(f"🔹 [MockServerClient] Requesting: {url}")
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ [MockServerClient] Success: {url} - Status: {response.status_code} - Data keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict response'}")
            return data
        except httpx.RequestError as e:
            logger.error(f"❌ [MockServerClient] Network error calling {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ [MockServerClient] HTTP error {e.response.status_code} from {url}: {e.response.text}")
            raise
    
    def _extract_mac_address(self, device_name: str) -> str:
        """
        Extract MAC address from device name.
        
        Args:
            device_name: Device name (e.g., "SEP001122334455" or "CSFUSER")
            
        Returns:
            Clean MAC address string
        """
        if device_name.startswith("SEP"):
            return device_name[3:]  # Remove "SEP" prefix
        elif device_name.startswith("CSF"):
            # For CSF devices, return the full name as MAC address placeholder
            return device_name
        return device_name
    
    def _infer_device_type(self, device_name: str, model: Optional[str] = None) -> str:
        """
        Infer device type from name and model.
        
        Args:
            device_name: Device name
            model: Device model information
            
        Returns:
            Device type string
        """
        if device_name.startswith("CSF"):
            return "Softphone"
        elif device_name.startswith("SEP"):
            return "Phone"
        elif model and "jabber" in model.lower():
            return "Jabber"
        return "Unknown"
    
    def _transform_device_data(self, device_info: CUCMDevice) -> Dict:
        """
        Transform raw device info into CENSUS format.
        
        Args:
            device_info: Raw device information from mock server
            
        Returns:
            Transformed device dictionary
        """
        mac_address = self._extract_mac_address(device_info.name)
        device_type = self._infer_device_type(device_info.name, device_info.model)
        
        return {
            "name": device_info.name,
            "description": device_info.description,
            "mac_address": mac_address,
            "ip_address": device_info.ip_address,
            "model": device_info.model,
            "device_type": device_type,
            "owner_username": device_info.owner_username,
            "is_registered": device_info.ip_address is not None and device_info.ip_address != "",
            "status": "registered" if device_info.ip_address else "unregistered"
        }
    
    async def fetch_cucm_stats(self) -> Dict:
        """
        Fetch CUCM system statistics from mock server.

        Returns:
            Dictionary with CUCM statistics

        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        try:
            logger.info(f"📊 [MockServerClient] Fetching CUCM stats from: {self.base_url}")
            response_data = await self._make_request("/api/cucm/system/stats")
            logger.info(f"✅ [MockServerClient] Successfully fetched CUCM stats - Metrics: {list(response_data.get('metrics', {}).keys())}")
            return response_data

        except Exception as e:
            logger.error(f"❌ [MockServerClient] Failed to fetch CUCM stats: {e}")
            raise
    
    async def fetch_cms_stats(self) -> Dict:
        """
        Fetch CMS statistics from mock server.

        Returns:
            Dictionary with CMS statistics

        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        try:
            logger.info(f"📊 [MockServerClient] Fetching CMS stats from: {self.base_url}")
            response_data = await self._make_request("/api/cms/stats")
            logger.info(f"✅ [MockServerClient] Successfully fetched CMS stats - Metrics: {list(response_data.get('metrics', {}).keys())}")
            return response_data

        except Exception as e:
            logger.error(f"❌ [MockServerClient] Failed to fetch CMS stats: {e}")
            raise
    
    async def fetch_registered_endpoints(self) -> List[Dict]:
        """
        Fetch registered endpoints from mock server (simulated from CUCM stats).

        Returns:
            List of device dictionaries in CENSUS format

        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        try:
            logger.info(f"📱 [MockServerClient] Fetching registered endpoints")
            # Get CUCM stats which contains phone breakdown
            stats = await self.fetch_cucm_stats()

            # Extract phone breakdown from metrics
            phone_breakdown = stats.get("metrics", {}).get("phone_breakdown", {}).get("value", [])
            logger.info(f"📊 [MockServerClient] Phone breakdown locations: {len(phone_breakdown)}")

            # Transform phone breakdown into device list
            devices = []
            device_counter = 0

            for breakdown in phone_breakdown:
                location = breakdown.get("location_base", "Unknown")
                prefix = breakdown.get("prefix", "000")
                count = breakdown.get("registered_phone_count", 0)
                logger.info(f"📍 [MockServerClient] Location: {location}, Prefix: {prefix}, Count: {count}")

                # Generate mock devices based on breakdown
                for i in range(count):
                    device_counter += 1
                    device_name = f"SEP{prefix}{str(device_counter).zfill(8)}"

                    device_info = CUCMDevice(
                        name=device_name,
                        description=f"Phone at {location}",
                        model="Cisco 7841",
                        ip_address=f"10.55.{device_counter % 256}.{(device_counter // 256) % 256}",
                        owner_username=f"user{device_counter}"
                    )

                    transformed_device = self._transform_device_data(device_info)
                    devices.append(transformed_device)

            logger.info(f"✅ [MockServerClient] Successfully generated {len(devices)} devices from mock server stats")
            return devices

        except Exception as e:
            logger.error(f"❌ [MockServerClient] Failed to fetch endpoints: {e}")
            raise
    
    async def fetch_cucm_users(self) -> List[Dict]:
        """
        Fetch users from mock server (simulated).

        Returns:
            List of user dictionaries in CENSUS format

        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        try:
            logger.info(f"👥 [MockServerClient] Fetching CUCM users")
            # Generate mock users based on device count
            stats = await self.fetch_cucm_stats()
            phone_breakdown = stats.get("metrics", {}).get("phone_breakdown", {}).get("value", [])

            total_phones = sum(b.get("registered_phone_count", 0) for b in phone_breakdown)
            user_count = max(1, total_phones // 2)  # Roughly half the phones have users
            logger.info(f"📊 [MockServerClient] Total phones: {total_phones}, Generating users: {user_count}")

            users = []
            for i in range(user_count):
                user_info = CUCMUser(
                    userid=f"user{i+1}",
                    firstname=f"First{i+1}",
                    lastname=f"Last{i+1}",
                    department="IT",
                    status=1
                )

                transformed_user = self._transform_user_data(user_info)
                users.append(transformed_user)

            logger.info(f"✅ [MockServerClient] Successfully generated {len(users)} users from mock server")
            return users

        except Exception as e:
            logger.error(f"❌ [MockServerClient] Failed to fetch users: {e}")
            raise
    
    def _transform_user_data(self, user_info: CUCMUser) -> Dict:
        """
        Transform raw user info into CENSUS format.
        
        Args:
            user_info: Raw user information from mock server
            
        Returns:
            Transformed user dictionary
        """
        full_name = f"{user_info.firstname} {user_info.lastname}".strip()
        is_active = user_info.status == 1
        
        return {
            "ad_username": user_info.userid,
            "full_name": full_name,
            "department": user_info.department,
            "is_active": is_active
        }


# Singleton instance for dependency injection
async def get_mock_server_client() -> MockServerClient:
    """
    Dependency function to get mock server client instance.
    
    Usage:
        @app.get("/devices")
        async def get_devices(mock_client: MockServerClient = Depends(get_mock_server_client)):
            devices = await mock_client.fetch_registered_endpoints()
            return {"devices": devices}
    """
    return MockServerClient()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Test the mock server client."""
        client = MockServerClient()
        
        try:
            # Test connection
            health = await client._make_request("/health")
            print(f"✅ Mock server health: {health}")
            
            # Fetch CUCM stats
            cucm_stats = await client.fetch_cucm_stats()
            print(f"📊 CUCM Stats: {cucm_stats}")
            
            # Fetch CMS stats
            cms_stats = await client.fetch_cms_stats()
            print(f"📊 CMS Stats: {cms_stats}")
            
            # Fetch devices
            devices = await client.fetch_registered_endpoints()
            print(f"📱 Found {len(devices)} devices")
            
            # Fetch users
            users = await client.fetch_cucm_users()
            print(f"👥 Found {len(users)} users")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        finally:
            await client.close()
    
    # Run the test
    asyncio.run(main())
