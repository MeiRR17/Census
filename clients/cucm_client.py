"""
CUCM Client - Cisco Unified Communications Manager
Uses AXL API for phone and user management
"""
from typing import Dict, Any, List, Optional
from .base_client import BaseClient
from zeep import Client, Settings
from zeep.cache import SqliteCache
from zeep.transports import Transport
import requests
import logging

logger = logging.getLogger(__name__)

class CUCMClient(BaseClient):
    """Client for Cisco Unified Communications Manager via AXL API"""
    
    def __init__(self, host: str, username: str, password: str, 
                 version: str = "14.0", **kwargs):
        """
        Initialize CUCM client
        
        Args:
            host: CUCM server hostname/IP
            username: AXL API username
            password: AXL API password
            version: CUCM version for WSDL
        """
        super().__init__(host, username, password, **kwargs)
        self.version = version
        self.wsdl_url = f"https://{host}:8443/axl/schema/{version}/AXLAPI.wsdl"
        self.binding_name = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"
        self.service = None
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Initialize AXL service connection"""
        try:
            # Create session with SSL verification disabled
            session = requests.Session()
            session.verify = self.verify_ssl
            session.auth = (self.username, self.password)
            
            # Configure Zeep settings
            settings = Settings(
                strict=False,
                xml_huge_tree=True,
                force_https=(self.host.startswith("https://"))
            )
            
            # Create transport with session
            transport = Transport(
                session=session,
                operation_timeout=self.timeout,
                timeout=self.timeout
            )
            
            # Create Zeep client
            self.service = Client(
                wsdl=self.wsdl_url,
                transport=transport,
                settings=settings
            )
            
            # Create service binding
            self.service = self.service.create_service(
                self.binding_name,
                f"https://{self.host}:8443/axl/"
            )
            
            # Test connection
            self.service.executeSQLQuery("SELECT 1")
            
            self._authenticated = True
            logger.info(f"Successfully authenticated with CUCM: {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with CUCM: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to CUCM"""
        if not self._authenticated:
            return self.authenticate()
        
        try:
            self.service.executeSQLQuery("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"CUCM connection test failed: {e}")
            self._authenticated = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get CUCM status information"""
        try:
            # Get basic system info
            result = self.service.executeSQLQuery(
                "SELECT COUNT(*) as device_count FROM device"
            )
            
            device_count = int(result[0]['device_count'])
            
            return {
                "status": "connected" if self.test_connection() else "disconnected",
                "host": self.host,
                "version": self.version,
                "device_count": device_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get CUCM status: {e}")
            return {
                "status": "error",
                "host": self.host,
                "error": str(e)
            }
    
    def get_phones(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all phones from CUCM"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            # Simple phone query
            sql = """
                SELECT d.name, d.description, d.product, 
                       tm.name as model, rd.ipaddress,
                       eu.userid as owner_username
                FROM device d
                LEFT JOIN typemodel tm ON d.typemodel = tm.enum
                LEFT JOIN devicerd rd ON d.pkid = rd.fkdevice
                LEFT JOIN enduser eu ON d.fkenduser = eu.pkid
                WHERE d.tkclass = '1'
                ORDER BY d.name
            """
            
            if limit:
                sql += f" LIMIT {limit}"
            
            result = self.service.executeSQLQuery(sql)
            
            phones = []
            for row in result:
                phones.append({
                    "name": row.get("name"),
                    "description": row.get("description"),
                    "model": row.get("model"),
                    "ip_address": row.get("ipaddress"),
                    "owner_username": row.get("owner_username"),
                    "is_registered": row.get("ipaddress") is not None and row.get("ipaddress") != ""
                })
            
            return phones
            
        except Exception as e:
            logger.error(f"Failed to get phones from CUCM: {e}")
            raise
    
    def get_users(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all users from CUCM"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            sql = """
                SELECT userid, firstname, lastname, department, 
                       telephonenumber, mailid, status
                FROM enduser
                WHERE status = '1'
                ORDER BY userid
            """
            
            if limit:
                sql += f" LIMIT {limit}"
            
            result = self.service.executeSQLQuery(sql)
            
            users = []
            for row in result:
                users.append({
                    "user_id": row.get("userid"),
                    "first_name": row.get("firstname"),
                    "last_name": row.get("lastname"),
                    "department": row.get("department"),
                    "phone": row.get("telephonenumber"),
                    "email": row.get("mailid"),
                    "status": "active" if row.get("status") == "1" else "inactive"
                })
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to get users from CUCM: {e}")
            raise
    
    def add_phone(self, phone_data: Dict[str, Any]) -> bool:
        """Add a new phone to CUCM"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            # Basic phone addition
            result = self.service.addPhone(
                name=phone_data["name"],
                description=phone_data.get("description", ""),
                product=phone_data.get("product", "Cisco 8841"),
                devicePool=phone_data.get("device_pool", "Default"),
                location=phone_data.get("location", "Hub_None"),
                phoneTemplate=phone_data.get("phone_template", "Standard 8841 SIP"),
                protocol=phone_data.get("protocol", "SIP")
            )
            
            logger.info(f"Added phone {phone_data['name']} to CUCM")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add phone to CUCM: {e}")
            return False
    
    def update_phone(self, phone_name: str, phone_data: Dict[str, Any]) -> bool:
        """Update an existing phone in CUCM"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            result = self.service.updatePhone(
                name=phone_name,
                **phone_data
            )
            
            logger.info(f"Updated phone {phone_name} in CUCM")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update phone in CUCM: {e}")
            return False
    
    def delete_phone(self, phone_name: str) -> bool:
        """Delete a phone from CUCM"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            result = self.service.removePhone(name=phone_name)
            
            logger.info(f"Deleted phone {phone_name} from CUCM")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete phone from CUCM: {e}")
            return False
