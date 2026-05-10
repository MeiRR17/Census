"""
Census MeetingPlace Client - MeetingPlace SOAP API Client
"""
import requests
import logging
from typing import Dict, Any, List, Optional
from .base_client import BaseClient

logger = logging.getLogger(__name__)

class MeetingPlaceClient(BaseClient):
    """MeetingPlace SOAP API Client"""
    
    def __init__(self, host: str = None, username: str = None, password: str = None):
        # Support both direct parameters and environment variables
        host = host or os.getenv('MEETINGPLACE_HOST', 'localhost')
        port = os.getenv('MEETINGPLACE_PORT', '8080')
        self.base_url = f"https://{host}:{port}/MeetingPlace/ws/services/"
        self.username = username or os.getenv('MEETINGPLACE_USERNAME', 'admin')
        self.password = password or os.getenv('MEETINGPLACE_PASSWORD', 'admin')
        
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'text/xml',
            'SOAPAction': '""'
        })
    
    def _make_soap_request(self, service: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make SOAP request to MeetingPlace"""
        try:
            soap_envelope = self._build_soap_envelope(action, params)
            url = f"{self.base_url}{service}"
            
            response = self.session.post(url, data=soap_envelope)
            response.raise_for_status()
            
            return self._parse_soap_response(response.text)
        except Exception as e:
            logger.error(f"SOAP request failed: {e}")
            return {}
    
    def _build_soap_envelope(self, action: str, params: Dict[str, Any] = None) -> str:
        """Build SOAP envelope"""
        params_xml = ""
        if params:
            for key, value in params.items():
                params_xml += f"<{key}>{value}</{key}>"
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:meet="http://www.cisco.com/meetingplace">
    <soapenv:Header/>
    <soapenv:Body>
        <meet:{action}>
            {params_xml}
        </meet:{action}>
    </soapenv:Body>
</soapenv:Envelope>"""
    
    def _parse_soap_response(self, response_text: str) -> Dict[str, Any]:
        """Parse SOAP response"""
        # Simplified SOAP parsing - in production, use proper XML parsing
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response_text)
            
            # Extract data from SOAP response
            result = {}
            for child in root.iter():
                if child.text and child.tag not in ['soapenv:Envelope', 'soapenv:Body']:
                    result[child.tag] = child.text
            
            return result
        except Exception as e:
            logger.error(f"Failed to parse SOAP response: {e}")
            return {}
    
    def get_meetings(self) -> List[Dict[str, Any]]:
        """Get all meetings"""
        try:
            response = self._make_soap_request("MeetingService", "getMeetings")
            return response.get('meetings', [])
        except Exception as e:
            logger.error(f"Failed to get meetings: {e}")
            return []
    
    def create_meeting(self, title: str, start_time: str, duration: int, 
                      participants: List[str] = None) -> Dict[str, Any]:
        """Create a new meeting"""
        try:
            params = {
                'title': title,
                'startTime': start_time,
                'duration': str(duration),
                'participants': ','.join(participants or [])
            }
            return self._make_soap_request("MeetingService", "createMeeting", params)
        except Exception as e:
            logger.error(f"Failed to create meeting: {e}")
            return {}
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            response = self._make_soap_request("UserService", "getUsers")
            return response.get('users', [])
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        try:
            params = {'userId': user_id}
            return self._make_soap_request("UserService", "getUserProfile", params)
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {}
    
    def sync_devices(self) -> List[Dict[str, Any]]:
        """Sync MeetingPlace devices"""
        devices = []
        try:
            # MeetingPlace doesn't have traditional devices, but we can sync meeting rooms
            meetings = self.get_meetings()
            for meeting in meetings:
                device = {
                    'name': meeting.get('title', ''),
                    'ip_address': None,
                    'mac_address': None,
                    'device_type': 'meeting_room',
                    'status': meeting.get('status', 'scheduled'),
                    'source': 'meetingplace',
                    'raw_data': meeting
                }
                devices.append(device)
        except Exception as e:
            logger.error(f"Failed to sync MeetingPlace devices: {e}")
        return devices
    
    def sync_meetings(self) -> List[Dict[str, Any]]:
        """Sync MeetingPlace meetings"""
        meetings = []
        try:
            meeting_list = self.get_meetings()
            for meeting in meeting_list:
                synced_meeting = {
                    'meeting_id': meeting.get('meetingId', ''),
                    'name': meeting.get('title', ''),
                    'uri': meeting.get('meetingUri', ''),
                    'passcode': meeting.get('passcode', ''),
                    'status': meeting.get('status', 'scheduled'),
                    'participants': len(meeting.get('participants', [])),
                    'source': 'meetingplace',
                    'raw_data': meeting
                }
                meetings.append(synced_meeting)
        except Exception as e:
            logger.error(f"Failed to sync MeetingPlace meetings: {e}")
        return meetings
    
    def sync_users(self) -> List[Dict[str, Any]]:
        """Sync MeetingPlace users"""
        users = []
        try:
            user_list = self.get_users()
            for user in user_list:
                synced_user = {
                    'user_id': user.get('userId', ''),
                    'name': user.get('displayName', ''),
                    'email': user.get('email', ''),
                    'department': user.get('department', ''),
                    'phone': user.get('phone', ''),
                    'source': 'meetingplace',
                    'raw_data': user
                }
                users.append(synced_user)
        except Exception as e:
            logger.error(f"Failed to sync MeetingPlace users: {e}")
        return users
