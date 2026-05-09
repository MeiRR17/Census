"""
SBC Client - Oracle Communications Session Border Controller
REST API client for SBC management
Based on sbc_rest_client library
"""
from typing import Dict, Any, List, Optional, Union
from .base_client import BaseClient
import requests
import base64
import xml.etree.ElementTree as ET
from urllib3.exceptions import InsecureRequestWarning
import logging

logger = logging.getLogger(__name__)

class SBCClient(BaseClient):
    """Client for Oracle Communications Session Border Controller"""
    
    def __init__(self, host: str, username: str, password: str, 
                 api_version: str = "v1.1", **kwargs):
        """
        Initialize SBC client
        
        Args:
            host: SBC server hostname/IP
            username: Admin username
            password: Admin password
            api_version: REST API version
        """
        super().__init__(host, username, password, **kwargs)
        self.api_version = api_version
        self.base_url = f"https://{self.host}/rest/{api_version}"
        self._token = None
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with SBC and get access token"""
        try:
            # Disable SSL warnings if verification is disabled
            if not self.verify_ssl:
                requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            
            # Get access token
            auth_url = f"{self.base_url}/auth/token"
            
            # Create basic auth header
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Accept": "application/xml",
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            response = requests.post(auth_url, headers=headers, 
                                  verify=self.verify_ssl, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.error(f"Token request failed: {response.status_code}")
                return False
            
            # Parse token from response
            root = ET.fromstring(response.text)
            token_elements = root.xpath("//accessToken")
            
            if not token_elements:
                logger.error("No token found in response")
                return False
            
            self._token = token_elements[0].text
            self._authenticated = True
            
            # Set authorization header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/xml"
            })
            
            logger.info(f"Successfully authenticated with SBC: {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with SBC: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to SBC"""
        if not self._authenticated:
            return self.authenticate()
        
        try:
            response = self.session.get(f"{self.base_url}/system/status", 
                                      timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SBC connection test failed: {e}")
            self._authenticated = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get SBC status information"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.get(f"{self.base_url}/system/status")
            if response.status_code != 200:
                raise Exception(f"Status request failed: {response.status_code}")
            
            root = ET.fromstring(response.text)
            
            return {
                "status": "connected" if self.test_connection() else "disconnected",
                "host": self.host,
                "role": root.findtext("role"),
                "global_cps": self.global_cps,
                "global_sessions": self.global_con_sessions
            }
            
        except Exception as e:
            logger.error(f"Failed to get SBC status: {e}")
            return {
                "status": "error",
                "host": self.host,
                "error": str(e)
            }
    
    @property
    def global_cps(self) -> str:
        """Get global calls per second"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.get(f"{self.base_url}/statistics/kpis?type=globalSessions")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                cps = root.findtext("sysGlobalCPS")
                return cps or "0"
            return "0"
        except Exception as e:
            logger.error(f"Failed to get global CPS: {e}")
            return "0"
    
    @property
    def global_con_sessions(self) -> str:
        """Get global connected sessions"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.get(f"{self.base_url}/statistics/kpis?type=globalSessions")
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                sessions = root.findtext("sysGlobalConSessions")
                return sessions or "0"
            return "0"
        except Exception as e:
            logger.error(f"Failed to get global sessions: {e}")
            return "0"
    
    def get_config_elements(self, element_type: str, key_attribs: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get configuration elements"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            url = f"{self.base_url}/configuration/configElements?elementType={element_type}&running=true"
            if key_attribs:
                url += key_attribs
            
            response = self.session.get(url)
            if response.status_code != 200:
                raise Exception(f"Failed to get config elements: {response.status_code}")
            
            # Parse XML response
            root = ET.fromstring(response.text)
            elements = []
            
            for element in root.findall(".//configElement"):
                element_data = {
                    "type": element.findtext("elementType"),
                }
                
                for attr in element.findall("attribute"):
                    name = attr.findtext("name")
                    values = attr.findall("value")
                    if values:
                        element_data[name] = [v.text for v in values] if len(values) > 1 else values[0].text
                
                elements.append(element_data)
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to get config elements: {e}")
            return []
    
    def update_config_element(self, xml_str: str) -> bool:
        """Update configuration element"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.put(
                f"{self.base_url}/configuration/configElements",
                data=xml_str,
                headers={"Content-Type": "application/xml"}
            )
            
            if response.status_code == 200:
                logger.info("Successfully updated SBC configuration element")
                return True
            else:
                logger.error(f"Failed to update config element: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update SBC config element: {e}")
            return False
    
    def add_config_element(self, xml_str: str) -> bool:
        """Add configuration element"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.post(
                f"{self.base_url}/configuration/configElements",
                data=xml_str,
                headers={"Content-Type": "application/xml"}
            )
            
            if response.status_code == 200:
                logger.info("Successfully added SBC configuration element")
                return True
            else:
                logger.error(f"Failed to add config element: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add SBC config element: {e}")
            return False
    
    def delete_config_element(self, element_type: str, key_attribs: str) -> bool:
        """Delete configuration element"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            url = f"{self.base_url}/configuration/configElements?elementType={element_type}{key_attribs}"
            response = self.session.delete(url)
            
            if response.status_code == 204:
                logger.info(f"Successfully deleted SBC config element: {element_type}")
                return True
            else:
                logger.error(f"Failed to delete config element: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete SBC config element: {e}")
            return False
    
    def lock_config(self) -> bool:
        """Lock configuration for changes"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.post(f"{self.base_url}/configuration/lock")
            
            if response.status_code == 204:
                logger.info("Successfully locked SBC configuration")
                return True
            else:
                logger.error(f"Failed to lock config: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to lock SBC config: {e}")
            return False
    
    def unlock_config(self) -> bool:
        """Unlock configuration"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.post(f"{self.base_url}/configuration/unlock")
            
            if response.status_code == 204:
                logger.info("Successfully unlocked SBC configuration")
                return True
            else:
                logger.error(f"Failed to unlock config: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to unlock SBC config: {e}")
            return False
    
    def activate_config(self) -> bool:
        """Activate configuration changes"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.post(f"{self.base_url}/configuration/management?action=activate")
            
            if response.status_code == 200:
                logger.info("Successfully activated SBC configuration")
                return True
            else:
                logger.error(f"Failed to activate config: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to activate SBC config: {e}")
            return False
    
    def reboot(self) -> bool:
        """Reboot the SBC"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.session.post(f"{self.base_url}/admin/reboot")
            
            if response.status_code == 200:
                logger.info("Successfully initiated SBC reboot")
                return True
            else:
                logger.error(f"Failed to reboot SBC: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to reboot SBC: {e}")
            return False
