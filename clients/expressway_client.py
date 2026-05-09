"""
Expressway Client - Cisco Expressway (VCS)
REST API client for video conferencing infrastructure
"""
from typing import Dict, Any, List, Optional
from .base_client import BaseClient
import json
import logging

logger = logging.getLogger(__name__)

class ExpresswayClient(BaseClient):
    """Client for Cisco Expressway REST API"""
    
    def __init__(self, host: str, username: str, password: str, **kwargs):
        """
        Initialize Expressway client
        
        Args:
            host: Expressway server hostname/IP
            username: Admin username
            password: Admin password
        """
        super().__init__(host, username, password, **kwargs)
        self.base_url = f"https://{self.host}:443/api"
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Test authentication with Expressway"""
        try:
            # Test with system status endpoint
            response = self.get("status")
            if response.status_code == 200:
                self._authenticated = True
                logger.info(f"Successfully authenticated with Expressway: {self.host}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to authenticate with Expressway: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Expressway"""
        if not self._authenticated:
            return self.authenticate()
        
        try:
            response = self.get("status")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Expressway connection test failed: {e}")
            self._authenticated = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get Expressway status information"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("status")
            if response.status_code != 200:
                raise Exception(f"Status request failed: {response.status_code}")
            
            status_data = response.json()
            
            return {
                "status": "connected" if self.test_connection() else "disconnected",
                "host": self.host,
                "version": status_data.get("version"),
                "uptime": status_data.get("uptime"),
                "cpu_usage": status_data.get("cpu_usage"),
                "memory_usage": status_data.get("memory_usage")
            }
            
        except Exception as e:
            logger.error(f"Failed to get Expressway status: {e}")
            return {
                "status": "error",
                "host": self.host,
                "error": str(e)
            }
    
    def get_registrations(self) -> List[Dict[str, Any]]:
        """Get all registered endpoints"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("registrations")
            if response.status_code != 200:
                raise Exception(f"Failed to get registrations: {response.status_code}")
            
            data = response.json()
            registrations = data.get("registrations", [])
            
            return [{
                "endpoint_id": reg.get("id"),
                "name": reg.get("name"),
                "uri": reg.get("uri"),
                "ip_address": reg.get("ip"),
                "status": reg.get("status"),
                "device_type": reg.get("device_type")
            } for reg in registrations]
            
        except Exception as e:
            logger.error(f"Failed to get registrations from Expressway: {e}")
            raise
    
    def get_calls(self) -> List[Dict[str, Any]]:
        """Get all active calls"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("calls")
            if response.status_code != 200:
                raise Exception(f"Failed to get calls: {response.status_code}")
            
            data = response.json()
            calls = data.get("calls", [])
            
            return [{
                "call_id": call.get("id"),
                "caller": call.get("caller"),
                "callee": call.get("callee"),
                "start_time": call.get("start_time"),
                "duration": call.get("duration"),
                "status": call.get("status")
            } for call in calls]
            
        except Exception as e:
            logger.error(f"Failed to get calls from Expressway: {e}")
            raise
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users from Expressway"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("users")
            if response.status_code != 200:
                raise Exception(f"Failed to get users: {response.status_code}")
            
            data = response.json()
            users = data.get("users", [])
            
            return [{
                "user_id": user.get("id"),
                "username": user.get("username"),
                "name": user.get("name"),
                "email": user.get("email"),
                "department": user.get("department")
            } for user in users]
            
        except Exception as e:
            logger.error(f"Failed to get users from Expressway: {e}")
            raise
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user in Expressway"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.post("users", data=user_data)
            
            if response.status_code == 201:
                logger.info(f"Created user {user_data.get('username')} in Expressway")
                return True
            else:
                logger.error(f"Failed to create user: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create user in Expressway: {e}")
            return False
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Update an existing user in Expressway"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.put(f"users/{user_id}", data=user_data)
            
            if response.status_code == 200:
                logger.info(f"Updated user {user_id} in Expressway")
                return True
            else:
                logger.error(f"Failed to update user: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update user in Expressway: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user from Expressway"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.delete(f"users/{user_id}")
            
            if response.status_code == 200:
                logger.info(f"Deleted user {user_id} from Expressway")
                return True
            else:
                logger.error(f"Failed to delete user: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete user in Expressway: {e}")
            return False
