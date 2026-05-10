"""
Census CMS Client - Simple REST API Client for Edge Apps
Supports both REST/JSON and XML formats
"""
import requests
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from .base_client import BaseClient
import os

logger = logging.getLogger(__name__)

class CMSClient(BaseClient):
    """Complete CMS REST Client supporting JSON and XML"""
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None):
        # Support both direct parameters and environment variables
        host = os.getenv('CMS_HOST', 'localhost')
        port = os.getenv('CMS_PORT', '8443')
        self.base_url = base_url or f"https://{host}:{port}"
        self.username = username or os.getenv('CMS_USERNAME', 'admin')
        self.password = password or os.getenv('CMS_PASSWORD', 'admin')
        self.timeout = 30
        self.verify_ssl = False  # For self-signed certs
        
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.session.verify = self.verify_ssl
        
        # Disable SSL warnings for self-signed certs
        if not self.verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Core HTTP Methods
    def cms_get(self, endpoint: str) -> requests.Response:
        """Make GET request to CMS API"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        return self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
    
    def cms_post(self, endpoint: str, json_data: Dict = None) -> requests.Response:
        """Make POST request to CMS API"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        return self.session.post(url, json=json_data, timeout=self.timeout, verify=self.verify_ssl)
    
    def cms_put(self, endpoint: str, json_data: Dict = None) -> requests.Response:
        """Make PUT request to CMS API"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        return self.session.put(url, json=json_data, timeout=self.timeout, verify=self.verify_ssl)
    
    def cms_delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request to CMS API"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        return self.session.delete(url, timeout=self.timeout, verify=self.verify_ssl)
    
    # CoSpace Management
    def get_cospaces(self) -> List[Dict]:
        """Get all CoSpaces"""
        response = self.cms_get('coSpaces')
        if response.status_code == 200:
            return response.json().get('coSpace', [])
        else:
            logger.error(f"Failed to get CoSpaces: {response.status_code}")
            return []
    
    def create_cospace(self, name: str, uri: str = None, passcode: str = None, 
                      auto_attendant: bool = False) -> Dict:
        """Create a new CoSpace"""
        data = {
            'name': name,
            'uri': uri or name.lower().replace(' ', '-'),
            'passcode': passcode or '123456',
            'autoAttendant': auto_attendant
        }
        
        response = self.cms_post('coSpaces', json_data=data)
        if response.status_code == 201:
            return response.json()
        else:
            logger.error(f"Failed to create CoSpace: {response.status_code}")
            return {}
    
    def get_cospace_details(self, cospace_id: str) -> Dict:
        """Get CoSpace details"""
        response = self.cms_get(f'coSpaces/{cospace_id}')
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get CoSpace details: {response.status_code}")
            return {}
    
    def update_cospace(self, cospace_id: str, **kwargs) -> Dict:
        """Update CoSpace"""
        response = self.cms_put(f'coSpaces/{cospace_id}', json_data=kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to update CoSpace: {response.status_code}")
            return {}
    
    def delete_cospace(self, cospace_id: str) -> bool:
        """Delete CoSpace"""
        response = self.cms_delete(f'coSpaces/{cospace_id}')
        return response.status_code == 204
    
    # Call Management
    def get_active_calls(self) -> List[Dict]:
        """Get all active calls"""
        response = self.cms_get('calls')
        if response.status_code == 200:
            return response.json().get('call', [])
        else:
            logger.error(f"Failed to get active calls: {response.status_code}")
            return []
    
    def get_call_details(self, call_id: str) -> Dict:
        """Get call details"""
        response = self.cms_get(f'calls/{call_id}')
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get call details: {response.status_code}")
            return {}
    
    def get_call_participants(self, call_id: str) -> List[Dict]:
        """Get call participants"""
        response = self.cms_get(f'calls/{call_id}/participants')
        if response.status_code == 200:
            return response.json().get('participant', [])
        else:
            logger.error(f"Failed to get call participants: {response.status_code}")
            return []
    
    # Participant Management
    def mute_participant(self, call_id: str, participant_id: str, mute: bool = True) -> bool:
        """Mute or unmute a participant"""
        data = {'mute': mute}
        response = self.cms_put(f'calls/{call_id}/participants/{participant_id}', json_data=data)
        return response.status_code == 200
    
    def kick_participant(self, call_id: str, participant_id: str) -> bool:
        """Kick a participant from call"""
        response = self.cms_delete(f'calls/{call_id}/participants/{participant_id}')
        return response.status_code == 204
    
    # System Information
    def test_connection(self) -> bool:
        """Test connection to CMS"""
        try:
            response = self.cms_get('system/status')
            return response.status_code == 200
        except Exception as e:
            logger.error(f"CMS connection test failed: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Get CMS system information"""
        response = self.cms_get('system')
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get system info: {response.status_code}")
            return {}
    
    # Simple methods for edge apps
    def get_meetings(self) -> List[Dict]:
        """Get meetings (alias for active calls)"""
        return self.get_active_calls()
    
    def get_devices(self) -> List[Dict]:
        """Get devices (alias for cospaces)"""
        cospaces = self.get_cospaces()
        devices = []
        for cospace in cospaces:
            device = {
                'id': cospace.get('id', ''),
                'name': cospace.get('name', ''),
                'type': 'cospace',
                'status': cospace.get('status', 'unknown'),
                'uri': cospace.get('uri', ''),
                'source': 'cms'
            }
            devices.append(device)
        return devices
    
    @classmethod
    def create_default(cls) -> 'CMSClient':
        """Create CMS client with default configuration"""
        return cls()
    
    @classmethod
    def create_from_env(cls) -> 'CMSClient':
        """Create CMS client from environment variables"""
        return cls(
            base_url=os.getenv('CMS_URL'),
            username=os.getenv('CMS_USERNAME'),
            password=os.getenv('CMS_PASSWORD')
        )
    
    def get_config_summary(self) -> Dict:
        """Get current configuration summary"""
        return {
            "base_url": self.base_url,
            "username": self.username,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl,
            "connected": self.test_connection()
        }
    
    # =====================================================
    # XML Methods (from services/cms_service.py)
    # =====================================================
    
    def update_cospace_passcode(self, cospace_id: str, passcode: str) -> Dict[str, Any]:
        """Update CoSpace passcode using XML"""
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <coSpace>
            <passcode>{passcode}</passcode>
        </coSpace>'''
        
        response = self.cms_put(f'coSpaces/{cospace_id}', json_data={'passcode': passcode})
        if response.status_code == 200:
            try:
                return self._parse_xml_response(response.text)
            except:
                return {'success': True}
        else:
            logger.error(f"Failed to update CoSpace passcode: {response.status_code}")
            return {}
    
    def list_cospaces(self) -> List[Dict[str, Any]]:
        """List all CoSpaces with XML parsing"""
        response = self.cms_get('coSpaces')
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.text)
                cospaces = []
                for cospace in root.findall('coSpace'):
                    cospaces.append(self._xml_element_to_dict(cospace))
                return cospaces
            except:
                # Fallback to JSON
                return response.json().get('coSpace', [])
        else:
            logger.error(f"Failed to list CoSpaces: {response.status_code}")
            return []
    
    # Utility Methods
    def _parse_xml_response(self, xml_text: str) -> Dict:
        """Parse XML response to dictionary"""
        try:
            root = ET.fromstring(xml_text)
            return self._xml_element_to_dict(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            raise Exception(f"Invalid XML response: {e}")
    
    def _xml_element_to_dict(self, element: ET.Element) -> Dict:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            else:
                result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
