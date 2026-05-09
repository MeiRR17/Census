"""
UCCX Client - Cisco Unified Contact Center Express
REST API client for contact center management
"""
from typing import Dict, Any, List, Optional
from .base_client import BaseClient
import json
import logging

logger = logging.getLogger(__name__)

class UCCXClient(BaseClient):
    """Client for Cisco Unified Contact Center Express REST API"""
    
    def __init__(self, host: str, username: str, password: str, **kwargs):
        """
        Initialize UCCX client
        
        Args:
            host: UCCX server hostname/IP
            username: API username
            password: API password
        """
        super().__init__(host, username, password, **kwargs)
        self.base_url = f"https://{self.host}:8445/adminapi"
        self._authenticated = False
    
    def authenticate(self) -> bool:
        """Test authentication with UCCX"""
        try:
            # Test with a simple API call
            response = self.get("team")
            if response.status_code == 200:
                self._authenticated = True
                logger.info(f"Successfully authenticated with UCCX: {self.host}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to authenticate with UCCX: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to UCCX"""
        if not self._authenticated:
            return self.authenticate()
        
        try:
            response = self.get("team")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"UCCX connection test failed: {e}")
            self._authenticated = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get UCCX status information"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            # Get system info
            response = self.get("systeminfo")
            if response.status_code != 200:
                raise Exception(f"System info request failed: {response.status_code}")
            
            system_info = response.json()
            
            return {
                "status": "connected" if self.test_connection() else "disconnected",
                "host": self.host,
                "version": system_info.get("version"),
                "uptime": system_info.get("uptime")
            }
            
        except Exception as e:
            logger.error(f"Failed to get UCCX status: {e}")
            return {
                "status": "error",
                "host": self.host,
                "error": str(e)
            }
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agents from UCCX"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("agent")
            if response.status_code != 200:
                raise Exception(f"Failed to get agents: {response.status_code}")
            
            data = response.json()
            agents = data.get("agent", [])
            
            return [{
                "agent_id": agent.get("agentId"),
                "first_name": agent.get("firstName"),
                "last_name": agent.get("lastName"),
                "extension": agent.get("extension"),
                "status": agent.get("state")
            } for agent in agents]
            
        except Exception as e:
            logger.error(f"Failed to get agents from UCCX: {e}")
            raise
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams from UCCX"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("team")
            if response.status_code != 200:
                raise Exception(f"Failed to get teams: {response.status_code}")
            
            data = response.json()
            teams = data.get("team", [])
            
            return [{
                "team_id": team.get("teamId"),
                "name": team.get("teamName"),
                "supervisor": team.get("supervisorId")
            } for team in teams]
            
        except Exception as e:
            logger.error(f"Failed to get teams from UCCX: {e}")
            raise
    
    def get_queues(self) -> List[Dict[str, Any]]:
        """Get all CSQs (Contact Service Queues) from UCCX"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.get("csq")
            if response.status_code != 200:
                raise Exception(f"Failed to get queues: {response.status_code}")
            
            data = response.json()
            queues = data.get("csq", [])
            
            return [{
                "queue_id": queue.get("csqId"),
                "name": queue.get("csqName"),
                "description": queue.get("description"),
                "service_level": queue.get("serviceLevel")
            } for queue in queues]
            
        except Exception as e:
            logger.error(f"Failed to get queues from UCCX: {e}")
            raise
    
    def create_agent(self, agent_data: Dict[str, Any]) -> bool:
        """Create a new agent in UCCX"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.post("agent", data=agent_data)
            
            if response.status_code == 201:
                logger.info(f"Created agent {agent_data.get('agentId')} in UCCX")
                return True
            else:
                logger.error(f"Failed to create agent: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create agent in UCCX: {e}")
            return False
    
    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> bool:
        """Update an existing agent in UCCX"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.put(f"agent/{agent_id}", data=agent_data)
            
            if response.status_code == 200:
                logger.info(f"Updated agent {agent_id} in UCCX")
                return True
            else:
                logger.error(f"Failed to update agent: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update agent in UCCX: {e}")
            return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent from UCCX"""
        try:
            if not self._authenticated:
                self.authenticate()
            
            response = self.delete(f"agent/{agent_id}")
            
            if response.status_code == 200:
                logger.info(f"Deleted agent {agent_id} from UCCX")
                return True
            else:
                logger.error(f"Failed to delete agent: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete agent in UCCX: {e}")
            return False
