"""
AXLerate Client - HTTP REST client for Cisco CUCM integration.
Acts as an async HTTP client to the AXLerate microservice.
"""

import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from core.config import get_settings


logger = logging.getLogger(__name__)


class DeviceInfo(BaseModel):
    """Pydantic model for device information from AXLerate."""
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    owner_username: Optional[str] = None


class UserInfo(BaseModel):
    """Pydantic model for user information from AXLerate."""
    userid: str
    firstname: str
    lastname: str
    department: Optional[str] = None
    status: int


class AXLerateClient:
    """
    Async HTTP client for AXLerate microservice.
    Provides methods to fetch device information from Cisco CUCM.
    """
    
    def __init__(self, base_url: Optional[str] = None, sql_endpoint: Optional[str] = None):
        """
        Initialize the AXLerate client.
        
        Args:
            base_url: Base URL of the AXLerate service. If None, uses config.
            sql_endpoint: SQL query endpoint. If None, uses default.
        """
        self.settings = get_settings()
        self.base_url = base_url or self.settings.axlerate_base_url
        self.sql_endpoint = sql_endpoint or "/axl/sql/query"  # Standard AXLerate endpoint
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
    
    async def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """
        Make an HTTP POST request to AXLerate.
        
        Args:
            endpoint: API endpoint to call
            data: JSON payload to send
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Network error calling AXLerate {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from AXLerate {url}: {e.response.text}")
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
    
    def _transform_device_data(self, device_info: DeviceInfo) -> Dict:
        """
        Transform raw device info into CENSUS format.
        
        Args:
            device_info: Raw device information from AXLerate
            
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
    
    async def fetch_registered_endpoints(self) -> List[Dict]:
        """
        Fetch registered endpoints from CUCM via AXLerate.
        
        Returns:
            List of device dictionaries in CENSUS format
            
        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
            ValueError: For malformed response data
        """
        sql_query = (
            "SELECT d.name, d.description, tm.name as model, rd.ipaddress, eu.userid "
            "FROM device d "
            "LEFT JOIN typemodel tm ON d.tkmodel = tm.enum "
            "LEFT JOIN registrationdynamic rd ON rd.fkdevice = d.pkid "
            "LEFT JOIN enduser eu ON d.fkenduser = eu.pkid "
            "WHERE d.tkclass = 1"
        )
        
        payload = {"sql": sql_query}
        
        try:
            logger.info(f"Fetching endpoints from AXLerate: {self.base_url}")
            response_data = await self._make_request(self.sql_endpoint, payload)
            
            # Extract the executeSQLQuery data from response
            if "executeSQLQuery" not in response_data:
                logger.error("Invalid response format: missing 'executeSQLQuery' field")
                raise ValueError("Invalid response format from AXLerate")
            
            query_result = response_data["executeSQLQuery"]
            
            # Handle different response formats
            if isinstance(query_result, dict) and "row" in query_result:
                rows = query_result["row"]
            elif isinstance(query_result, list):
                rows = query_result
            else:
                logger.error(f"Unexpected response format: {type(query_result)}")
                raise ValueError("Unexpected response format from AXLerate")
            
            # Ensure rows is a list
            if not isinstance(rows, list):
                rows = [rows] if rows else []
            
            logger.info(f"Received {len(rows)} devices from AXLerate")
            
            # Transform each device
            transformed_devices = []
            for row in rows:
                try:
                    device_info = DeviceInfo(**row)
                    transformed_device = self._transform_device_data(device_info)
                    transformed_devices.append(transformed_device)
                except Exception as e:
                    logger.warning(f"Failed to transform device data {row}: {e}")
                    continue
            
            logger.info(f"Successfully transformed {len(transformed_devices)} devices")
            return transformed_devices
            
        except Exception as e:
            logger.error(f"Failed to fetch endpoints from AXLerate: {e}")
            raise
    
    async def fetch_cucm_users(self) -> List[Dict]:
        """
        Fetch users from CUCM via AXLerate.
        
        Returns:
            List of user dictionaries in CENSUS format
            
        Raises:
            httpx.RequestError: For network-related errors
            httpx.HTTPStatusError: For HTTP error status codes
            ValueError: For malformed response data
        """
        sql_query = (
            "SELECT userid, firstname, lastname, department, status "
            "FROM enduser"
        )
        
        payload = {"sql": sql_query}
        
        try:
            logger.info(f"Fetching users from AXLerate: {self.base_url}")
            response_data = await self._make_request(self.sql_endpoint, payload)
            
            # Extract executeSQLQuery data from response
            if "executeSQLQuery" not in response_data:
                logger.error("Invalid response format: missing 'executeSQLQuery' field")
                raise ValueError("Invalid response format from AXLerate")
            
            query_result = response_data["executeSQLQuery"]
            
            # Handle different response formats
            if isinstance(query_result, dict) and "row" in query_result:
                rows = query_result["row"]
            elif isinstance(query_result, list):
                rows = query_result
            else:
                logger.error(f"Unexpected response format: {type(query_result)}")
                raise ValueError("Unexpected response format from AXLerate")
            
            # Ensure rows is a list
            if not isinstance(rows, list):
                rows = [rows] if rows else []
            
            logger.info(f"Received {len(rows)} users from AXLerate")
            
            # Transform each user
            transformed_users = []
            for row in rows:
                try:
                    user_info = UserInfo(**row)
                    transformed_user = self._transform_user_data(user_info)
                    transformed_users.append(transformed_user)
                except Exception as e:
                    logger.warning(f"Failed to transform user data {row}: {e}")
                    continue
            
            logger.info(f"Successfully transformed {len(transformed_users)} users")
            return transformed_users
            
        except Exception as e:
            logger.error(f"Failed to fetch users from AXLerate: {e}")
            raise
    
    def _transform_user_data(self, user_info: UserInfo) -> Dict:
        """
        Transform raw user info into CENSUS format.
        
        Args:
            user_info: Raw user information from AXLerate
            
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
async def get_axlerate_client() -> AXLerateClient:
    """
    Dependency function to get AXLerate client instance.
    
    Usage:
        @app.get("/devices")
        async def get_devices(axl: AXLerateClient = Depends(get_axlerate_client)):
            devices = await axl.fetch_registered_endpoints()
            return {"devices": devices}
    """
    return AXLerateClient()
