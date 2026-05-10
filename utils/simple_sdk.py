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
    
    # =====================================================
    # CMS Control Operations (via Census Proxy)
    # =====================================================
    
    def get_cms_cospaces(self) -> List[Dict]:
        """Get all CMS CoSpaces"""
        return self._request("GET", "/api/cms/cospaces")
    
    def create_cms_cospace(self, name: str, uri: Optional[str] = None, 
                          passcode: Optional[str] = None, **kwargs) -> Dict:
        """Create a new CMS CoSpace through Census"""
        data = {
            "name": name,
            "uri": uri,
            "passcode": passcode,
            **kwargs
        }
        return self._request("POST", "/api/cms/cospaces", data)
    
    def get_cms_cospace(self, cospace_id: str) -> Dict:
        """Get specific CoSpace details"""
        return self._request("GET", f"/api/cms/cospaces/{cospace_id}")
    
    def update_cospace_passcode(self, cospace_id: str, passcode: str) -> Dict:
        """Update CoSpace passcode"""
        return self._request("PUT", f"/api/cms/cospaces/{cospace_id}/passcode", 
                           {"passcode": passcode})
    
    def delete_cms_cospace(self, cospace_id: str) -> Dict:
        """Delete a CoSpace"""
        return self._request("DELETE", f"/api/cms/cospaces/{cospace_id}")
    
    def get_cms_calls(self) -> List[Dict]:
        """Get all CMS calls from database"""
        return self._request("GET", "/api/cms/calls")
    
    def get_cms_active_calls(self) -> Dict:
        """Get active calls from CMS in real-time"""
        return self._request("GET", "/api/cms/calls/active")
    
    def get_cms_call_details(self, call_id: str) -> Dict:
        """Get call details from CMS"""
        return self._request("GET", f"/api/cms/calls/{call_id}")
    
    def get_cms_call_participants(self, call_id: str) -> Dict:
        """Get participants for a specific call"""
        return self._request("GET", f"/api/cms/calls/{call_id}/participants")
    
    def mute_cms_participant(self, call_id: str, participant_name: str) -> Dict:
        """Mute a participant in a call"""
        return self._request("POST", 
                           f"/api/cms/calls/{call_id}/participants/{participant_name}/mute")
    
    def unmute_cms_participant(self, call_id: str, participant_name: str) -> Dict:
        """Unmute a participant in a call"""
        return self._request("POST", 
                           f"/api/cms/calls/{call_id}/participants/{participant_name}/unmute")
    
    def kick_cms_participant(self, call_id: str, participant_name: str) -> Dict:
        """Kick a participant from a call"""
        return self._request("DELETE", 
                           f"/api/cms/calls/{call_id}/participants/{participant_name}")
    
    def get_cms_system_status(self) -> Dict:
        """Get CMS system status"""
        return self._request("GET", "/api/cms/system/status")
    
    # =====================================================
    # CUCM Control Operations (via Census Proxy)
    # =====================================================
    
    def get_cucm_phones(self, status: Optional[str] = None, 
                       device_pool: Optional[str] = None) -> List[Dict]:
        """Get CUCM phones with optional filtering"""
        params = ""
        if status:
            params += f"?status={status}"
        if device_pool:
            separator = "&" if params else "?"
            params += f"{separator}device_pool={device_pool}"
        return self._request("GET", f"/api/cucm/phones{params}")
    
    def create_cucm_phone(self, name: str, **kwargs) -> Dict:
        """Create a new phone in CUCM through Census"""
        data = {"name": name, **kwargs}
        return self._request("POST", "/api/cucm/phones", data)
    
    def get_cucm_phone(self, phone_uuid: str) -> Dict:
        """Get specific phone details"""
        return self._request("GET", f"/api/cucm/phones/{phone_uuid}")
    
    def get_cucm_lines(self, pattern: Optional[str] = None) -> List[Dict]:
        """Get CUCM lines with optional filtering"""
        params = f"?pattern={pattern}" if pattern else ""
        return self._request("GET", f"/api/cucm/lines{params}")
    
    def create_cucm_line(self, pattern: str, **kwargs) -> Dict:
        """Create a new line in CUCM through Census"""
        data = {"pattern": pattern, **kwargs}
        return self._request("POST", "/api/cucm/lines", data)
    
    def get_cucm_line(self, line_uuid: str) -> Dict:
        """Get specific line details"""
        return self._request("GET", f"/api/cucm/lines/{line_uuid}")
    
    def get_cucm_users(self, department: Optional[str] = None) -> List[Dict]:
        """Get CUCM users with optional filtering"""
        params = f"?department={department}" if department else ""
        return self._request("GET", f"/api/cucm/users{params}")
    
    def create_cucm_user(self, user_id: str, **kwargs) -> Dict:
        """Create a new user in CUCM through Census"""
        data = {"user_id": user_id, **kwargs}
        return self._request("POST", "/api/cucm/users", data)
    
    def get_cucm_user(self, user_id: str) -> Dict:
        """Get specific user details"""
        return self._request("GET", f"/api/cucm/users/{user_id}")
    
    def get_cucm_system_status(self) -> Dict:
        """Get CUCM system status"""
        return self._request("GET", "/api/cucm/system/status")
    
    # =====================================================
    # UCCX Control Operations (via Census Proxy)
    # =====================================================
    
    def get_uccx_agents(self) -> Dict:
        """Get all UCCX agents"""
        return self._request("GET", "/api/uccx/agents")
    
    def create_uccx_agent(self, agent_id: str, first_name: str, last_name: str, 
                         extension: str, **kwargs) -> Dict:
        """Create a new UCCX agent through Census"""
        data = {
            "agent_id": agent_id,
            "first_name": first_name,
            "last_name": last_name,
            "extension": extension,
            **kwargs
        }
        return self._request("POST", "/api/uccx/agents", data)
    
    def update_uccx_agent(self, agent_id: str, **kwargs) -> Dict:
        """Update an existing UCCX agent"""
        return self._request("PUT", f"/api/uccx/agents/{agent_id}", kwargs)
    
    def delete_uccx_agent(self, agent_id: str) -> Dict:
        """Delete a UCCX agent"""
        return self._request("DELETE", f"/api/uccx/agents/{agent_id}")
    
    def get_uccx_teams(self) -> Dict:
        """Get all UCCX teams"""
        return self._request("GET", "/api/uccx/teams")
    
    def get_uccx_queues(self) -> Dict:
        """Get all UCCX queues (CSQs)"""
        return self._request("GET", "/api/uccx/queues")
    
    def get_uccx_system_status(self) -> Dict:
        """Get UCCX system status"""
        return self._request("GET", "/api/uccx/system/status")
    
    # =====================================================
    # Unified Operations
    # =====================================================
    
    def get_all_meetings(self) -> Dict:
        """Get all meetings from all systems"""
        return self._request("GET", "/api/unified/meetings")
    
    def get_all_devices(self) -> Dict:
        """Get all devices from all systems"""
        return self._request("GET", "/api/unified/devices")
    
    def get_all_users(self) -> Dict:
        """Get all users from all systems"""
        return self._request("GET", "/api/unified/users")
    
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


# Example usage - Comprehensive CMS/CUCM Control
if __name__ == "__main__":
    # Initialize SDK
    sdk = CensusSDK("http://localhost:8000")
    
    try:
        print("=" * 60)
        print("COMPREHENSIVE CENSUS SDK DEMO")
        print("=" * 60)
        
        # Check health
        print("\n1. Health Check:")
        health = sdk.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Database: {health.get('database')}")
        print(f"   Sync: {health.get('sync')}")
        
        # =====================================================
        # CMS OPERATIONS
        # =====================================================
        print("\n" + "=" * 60)
        print("CMS OPERATIONS")
        print("=" * 60)
        
        # Create a CoSpace
        print("\n2. Creating CMS CoSpace:")
        cospace = sdk.create_cms_cospace(
            name="Team Standup",
            uri="team-standup",
            passcode="123456",
            max_participants=25
        )
        print(f"   Created: {cospace.get('cospace', {}).get('name')}")
        
        # List all CoSpaces
        print("\n3. Listing CMS CoSpaces:")
        cospaces = sdk.get_cms_cospaces()
        print(f"   Found {len(cospaces)} CoSpaces")
        for cs in cospaces[:3]:  # Show first 3
            print(f"   - {cs.get('name')} ({cs.get('cospace_id')})")
        
        # Get active calls
        print("\n4. Getting Active Calls:")
        active_calls = sdk.get_cms_active_calls()
        calls = active_calls.get('active_calls', [])
        print(f"   Active calls: {len(calls)}")
        
        # If there are calls, control participants
        if calls:
            call_id = calls[0].get('callId', calls[0].get('id'))
            print(f"\n5. Controlling Call {call_id}:")
            
            # Get participants
            participants_data = sdk.get_cms_call_participants(call_id)
            participants = participants_data.get('participants', [])
            print(f"   Participants: {len(participants)}")
            
            if participants:
                participant_name = participants[0].get('name')
                print(f"\n   Muting participant: {participant_name}")
                result = sdk.mute_cms_participant(call_id, participant_name)
                print(f"   Result: {result.get('success')}")
        
        # Check CMS system status
        print("\n6. CMS System Status:")
        cms_status = sdk.get_cms_system_status()
        print(f"   Connected: {cms_status.get('connected')}")
        print(f"   Base URL: {cms_status.get('base_url')}")
        
        # =====================================================
        # CUCM OPERATIONS
        # =====================================================
        print("\n" + "=" * 60)
        print("CUCM OPERATIONS")
        print("=" * 60)
        
        # Create a phone
        print("\n7. Creating CUCM Phone:")
        phone = sdk.create_cucm_phone(
            name="SEP001122334455",
            description="John's Phone",
            model="Cisco 8841",
            device_pool="Default",
            protocol="SIP"
        )
        print(f"   Created: {phone.get('phone', {}).get('name')}")
        
        # List phones
        print("\n8. Listing CUCM Phones:")
        phones = sdk.get_cucm_phones(status="registered")
        print(f"   Found {len(phones)} registered phones")
        for p in phones[:3]:
            print(f"   - {p.get('name')} ({p.get('model')})")
        
        # Create a line
        print("\n9. Creating CUCM Line:")
        line = sdk.create_cucm_line(
            pattern="1234",
            description="Main Line",
            route_partition="Internal"
        )
        print(f"   Created: {line.get('line', {}).get('pattern')}")
        
        # List lines
        print("\n10. Listing CUCM Lines:")
        lines = sdk.get_cucm_lines(pattern="123")
        print(f"   Found {len(lines)} lines matching '123'")
        
        # Create a user
        print("\n11. Creating CUCM User:")
        user = sdk.create_cucm_user(
            user_id="john.doe",
            first_name="John",
            last_name="Doe",
            telephone_number="1234",
            department="Engineering"
        )
        print(f"   Created: {user.get('user', {}).get('display_name')}")
        
        # List users
        print("\n12. Listing CUCM Users:")
        users = sdk.get_cucm_users(department="Engineering")
        print(f"   Found {len(users)} users in Engineering")
        
        # Check CUCM system status
        print("\n13. CUCM System Status:")
        cucm_status = sdk.get_cucm_system_status()
        print(f"   Connected: {cucm_status.get('connected')}")
        
        # =====================================================
        # UNIFIED OPERATIONS
        # =====================================================
        print("\n" + "=" * 60)
        print("UNIFIED OPERATIONS")
        print("=" * 60)
        
        # Get all meetings
        print("\n14. All Meetings (Unified):")
        all_meetings = sdk.get_all_meetings()
        print(f"   CMS CoSpaces: {len(all_meetings.get('cms_cospaces', []))}")
        print(f"   Active Calls: {len(all_meetings.get('cms_active_calls', []))}")
        print(f"   Total: {all_meetings.get('total_meetings')}")
        
        # Get all devices
        print("\n15. All Devices (Unified):")
        all_devices = sdk.get_all_devices()
        print(f"   CUCM Phones: {len(all_devices.get('cucm_phones', []))}")
        print(f"   Total: {all_devices.get('total_devices')}")
        
        # Get all users
        print("\n16. All Users (Unified):")
        all_users = sdk.get_all_users()
        print(f"   CUCM Users: {len(all_users.get('cucm_users', []))}")
        print(f"   Total: {all_users.get('total_users')}")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
