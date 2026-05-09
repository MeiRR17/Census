"""
CMS Client - Cisco Meeting Server
REST API client for meeting management
"""
from typing import Dict, Any, List, Optional
from .base_client import BaseClient
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

class CMSClient(BaseClient):
    """Client for Cisco Meeting Server REST API"""
    
    def __init__(self, host: str, username: str, password: str, **kwargs):
        """
        Initialize CMS client
        
        Args:
            host: CMS server hostname/IP
            username: API username
            password: API password
        """
        super().__init__(host, username, password, **kwargs)
        self.base_url = f"{self.host}/api/v1/"
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Test authentication with CMS"""
        try:
            # Test with system status endpoint
            response = self.get("system/status")
            if response.status_code == 200:
                self._authenticated = True
                logger.info(f"Successfully authenticated with CMS: {self.host}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to authenticate with CMS: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to CMS"""
        if not self._authenticated:
            return self.authenticate()
        
        try:
            response = self.get("system/status")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"CMS connection test failed: {e}")
            self._authenticated = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get CMS status information"""
        try:
            response = self.get("system/status")
            if response.status_code != 200:
                raise Exception(f"Status request failed: {response.status_code}")
            
            root = ET.fromstring(response.text)
            
            return {
                "status": "connected" if self.test_connection() else "disconnected",
                "host": self.host,
                "total_participants": root.findtext(".//{*}callLegsActive"),
                "cpu_load": root.findtext(".//{*}cpuLoad"),
                "memory_usage": root.findtext(".//{*}memoryUsage")
            }
            
        except Exception as e:
            logger.error(f"Failed to get CMS status: {e}")
            return {
                "status": "error",
                "host": self.host,
                "error": str(e)
            }
    
    def get_meetings(self) -> List[Dict[str, Any]]:
        """Get all meetings from CMS"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("coSpaces")
            if response.status_code != 200:
                raise Exception(f"Failed to get meetings: {response.status_code}")
            
            return self._parse_meetings_xml(response.text)
            
        except Exception as e:
            logger.error(f"Failed to get meetings from CMS: {e}")
            raise
    
    def get_meeting_details(self, meeting_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific meeting"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get(f"coSpaces/{meeting_id}")
            if response.status_code != 200:
                raise Exception(f"Failed to get meeting details: {response.status_code}")
            
            root = ET.fromstring(response.text)
            
            return {
                "meeting_id": meeting_id,
                "name": root.findtext("name"),
                "uri": root.findtext("uri"),
                "passcode": root.findtext("passcode"),
                "secondary_uri": root.findtext("secondaryUri")
            }
            
        except Exception as e:
            logger.error(f"Failed to get meeting details from CMS: {e}")
            raise
    
    def create_meeting(self, meeting_data: Dict[str, Any]) -> bool:
        """Create a new meeting in CMS"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            # Prepare meeting data
            data = {
                "name": meeting_data["name"],
                "uri": meeting_data["meeting_id"],
                "callId": meeting_data["meeting_id"]
            }
            
            if meeting_data.get("passcode"):
                data["passcode"] = meeting_data["passcode"]
            
            response = self.post("coSpaces", data=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"Created meeting {meeting_data['meeting_id']} in CMS")
                return True
            else:
                logger.error(f"Failed to create meeting: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create meeting in CMS: {e}")
            return False
    
    def update_meeting(self, meeting_id: str, meeting_data: Dict[str, Any]) -> bool:
        """Update an existing meeting in CMS"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.put(f"coSpaces/{meeting_id}", data=meeting_data)
            
            if response.status_code == 200:
                logger.info(f"Updated meeting {meeting_id} in CMS")
                return True
            else:
                logger.error(f"Failed to update meeting: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update meeting in CMS: {e}")
            return False
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting from CMS"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.delete(f"coSpaces/{meeting_id}")
            
            if response.status_code == 200:
                logger.info(f"Deleted meeting {meeting_id} from CMS")
                return True
            else:
                logger.error(f"Failed to delete meeting: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete meeting in CMS: {e}")
            return False
    
    def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get all active calls in CMS"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("calls")
            if response.status_code != 200:
                raise Exception(f"Failed to get active calls: {response.status_code}")
            
            root = ET.fromstring(response.text)
            calls = []
            
            for call in root.findall("call"):
                call_id = call.get("id")
                
                # Get call details
                details_response = self.get(f"calls/{call_id}")
                if details_response.status_code == 200:
                    details_root = ET.fromstring(details_response.text)
                    
                    # Get participants count
                    legs_response = self.get(f"calls/{call_id}/callLegs")
                    participants = 0
                    if legs_response.status_code == 200:
                        legs_root = ET.fromstring(legs_response.text)
                        participants = len(legs_root.findall("callLeg"))
                    
                    calls.append({
                        "call_id": call_id,
                        "name": details_root.findtext("name"),
                        "participants": participants
                    })
            
            return calls
            
        except Exception as e:
            logger.error(f"Failed to get active calls from CMS: {e}")
            raise
    
    def _parse_meetings_xml(self, xml_string: str) -> List[Dict[str, Any]]:
        """Parse XML response for meetings list"""
        try:
            root = ET.fromstring(xml_string)
            meetings = []
            
            # Handle pagination if needed
            total_meetings = 0
            if root.get("total"):
                total_meetings = int(root.get("total"))
            
            for co_space in root.findall("coSpace"):
                meeting = {
                    "meeting_id": co_space.get("id"),
                    "name": co_space.findtext("name"),
                    "uri": co_space.findtext("uri"),
                    "call_id": co_space.findtext("callId"),
                    "auto_generated": co_space.findtext("autoGenerated")
                }
                meetings.append(meeting)
            
            # If pagination is needed, fetch additional pages
            current_count = len(meetings)
            while current_count < total_meetings:
                response = self.get(f"coSpaces?offset={current_count}&limit=20")
                if response.status_code != 200:
                    break
                
                additional_meetings = self._parse_meetings_xml(response.text)
                meetings.extend(additional_meetings[1:])  # Skip total count
                current_count += len(additional_meetings) - 1
            
            return meetings
            
        except Exception as e:
            logger.error(f"Failed to parse meetings XML: {e}")
            return []
