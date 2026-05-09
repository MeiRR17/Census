"""
Simple Census SDK for Edge Applications
Provides easy access to Census data and operations
"""
import requests
from typing import List, Dict, Any, Optional
import json

class CensusSDK:
    """Simple SDK for edge applications to interact with Census"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize Census SDK
        
        Args:
            base_url: Base URL of Census API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Internal request method"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def health_check(self) -> Dict:
        """Check Census API health"""
        return self._request("GET", "/health")
    
    # Device operations
    def get_devices(self, source: Optional[str] = None) -> List[Dict]:
        """Get all devices, optionally filtered by source"""
        params = f"?source={source}" if source else ""
        return self._request("GET", f"/api/devices{params}")
    
    def create_device(self, device_data: Dict) -> Dict:
        """Create or update a device"""
        return self._request("POST", "/api/devices", device_data)
    
    def update_device(self, device_name: str, device_data: Dict) -> Dict:
        """Update a specific device"""
        return self._request("PUT", f"/api/devices/{device_name}", device_data)
    
    def delete_device(self, device_name: str) -> Dict:
        """Delete a device"""
        return self._request("DELETE", f"/api/devices/{device_name}")
    
    # Meeting operations
    def get_meetings(self, source: Optional[str] = None) -> List[Dict]:
        """Get all meetings, optionally filtered by source"""
        params = f"?source={source}" if source else ""
        return self._request("GET", f"/api/meetings{params}")
    
    def create_meeting(self, meeting_data: Dict) -> Dict:
        """Create or update a meeting"""
        return self._request("POST", "/api/meetings", meeting_data)
    
    def update_meeting(self, meeting_id: str, meeting_data: Dict) -> Dict:
        """Update a specific meeting"""
        return self._request("PUT", f"/api/meetings/{meeting_id}", meeting_data)
    
    def delete_meeting(self, meeting_id: str) -> Dict:
        """Delete a meeting"""
        return self._request("DELETE", f"/api/meetings/{meeting_id}")
    
    # User operations
    def get_users(self, source: Optional[str] = None) -> List[Dict]:
        """Get all users, optionally filtered by source"""
        params = f"?source={source}" if source else ""
        return self._request("GET", f"/api/users{params}")
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create or update a user"""
        return self._request("POST", "/api/users", user_data)
    
    def update_user(self, user_id: str, user_data: Dict) -> Dict:
        """Update a specific user"""
        return self._request("PUT", f"/api/users/{user_id}", user_data)
    
    def delete_user(self, user_id: str) -> Dict:
        """Delete a user"""
        return self._request("DELETE", f"/api/users/{user_id}")
    
    # Sync operations
    def trigger_sync(self) -> Dict:
        """Trigger data sync with external servers"""
        return self._request("POST", "/api/sync")
    
    # Convenience methods for common operations
    def get_cucm_devices(self) -> List[Dict]:
        """Get all CUCM devices"""
        return self.get_devices(source="cucm")
    
    def get_cms_meetings(self) -> List[Dict]:
        """Get all CMS meetings"""
        return self.get_meetings(source="cms")
    
    def get_cucm_users(self) -> List[Dict]:
        """Get all CUCM users"""
        return self.get_users(source="cucm")
    
    def register_phone(self, name: str, ip_address: str, mac_address: str, model: str = "Unknown") -> Dict:
        """Register a new phone in CUCM"""
        device_data = {
            "name": name,
            "ip_address": ip_address,
            "mac_address": mac_address,
            "device_type": "Phone",
            "status": "registered",
            "source": "cucm",
            "raw_data": {"model": model}
        }
        return self.create_device(device_data)
    
    def create_meeting_room(self, meeting_id: str, name: str, passcode: Optional[str] = None) -> Dict:
        """Create a new meeting room in CMS"""
        meeting_data = {
            "meeting_id": meeting_id,
            "name": name,
            "uri": meeting_id,
            "passcode": passcode,
            "status": "active",
            "participants": 0,
            "source": "cms"
        }
        return self.create_meeting(meeting_data)


# Example usage
if __name__ == "__main__":
    # Initialize SDK
    sdk = CensusSDK("http://localhost:8000")
    
    try:
        # Check health
        health = sdk.health_check()
        print("Health:", health)
        
        # Get all devices
        devices = sdk.get_devices()
        print(f"Found {len(devices)} devices")
        
        # Register a new phone
        phone = sdk.register_phone(
            name="SEP001122334455",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55",
            model="Cisco 8841"
        )
        print("Registered phone:", phone)
        
        # Create a meeting
        meeting = sdk.create_meeting_room(
            meeting_id="CONF001",
            name="Test Conference",
            passcode="123456"
        )
        print("Created meeting:", meeting)
        
    except Exception as e:
        print(f"Error: {e}")
