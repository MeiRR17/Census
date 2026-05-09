"""
Sync Engine - Core synchronization logic for all systems
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import logging
from clients import (
    CUCMClient, CMSClient, MeetingPlaceClient, 
    UCCXClient, ExpresswayClient, SBCClient, TGWClient
)

logger = logging.getLogger(__name__)

class SyncEngine:
    """Core synchronization engine for all external systems"""
    
    def __init__(self, config: Dict[str, Dict[str, str]]):
        """
        Initialize sync engine with system configurations
        
        Args:
            config: Dictionary of system configurations
                {
                    "cucm": {"host": "...", "username": "...", "password": "..."},
                    "cms": {"host": "...", "username": "...", "password": "..."},
                    ...
                }
        """
        self.config = config
        self.clients = {}
        self.last_sync_times = {}
        self.sync_intervals = {
            "cucm": timedelta(minutes=5),
            "cms": timedelta(minutes=2),
            "meetingplace": timedelta(minutes=10),
            "uccx": timedelta(minutes=5),
            "expressway": timedelta(minutes=5),
            "sbc": timedelta(minutes=10),
            "tgw": timedelta(minutes=5)
        }
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all client connections"""
        client_classes = {
            "cucm": CUCMClient,
            "cms": CMSClient,
            "meetingplace": MeetingPlaceClient,
            "uccx": UCCXClient,
            "expressway": ExpresswayClient,
            "sbc": SBCClient,
            "tgw": TGWClient
        }
        
        for system_name, client_class in client_classes.items():
            if system_name in self.config:
                try:
                    config = self.config[system_name]
                    client = client_class(
                        host=config["host"],
                        username=config["username"],
                        password=config["password"]
                    )
                    
                    # Test connection
                    if client.authenticate():
                        self.clients[system_name] = client
                        logger.info(f"Connected to {system_name}: {config['host']}")
                    else:
                        logger.error(f"Failed to connect to {system_name}")
                        
                except Exception as e:
                    logger.error(f"Error initializing {system_name} client: {e}")
    
    def sync_all_systems(self) -> Dict[str, Any]:
        """Sync all systems and return consolidated data"""
        results = {}
        
        for system_name, client in self.clients.items():
            try:
                if self._should_sync(system_name):
                    logger.info(f"Starting sync for {system_name}")
                    system_data = self._sync_system(system_name, client)
                    results[system_name] = {
                        "status": "success",
                        "data": system_data,
                        "sync_time": datetime.now().isoformat()
                    }
                    self.last_sync_times[system_name] = datetime.now()
                else:
                    results[system_name] = {
                        "status": "skipped",
                        "message": "Sync not needed yet",
                        "last_sync": self.last_sync_times.get(system_name)
                    }
                    
            except Exception as e:
                logger.error(f"Failed to sync {system_name}: {e}")
                results[system_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def _should_sync(self, system_name: str) -> bool:
        """Check if system should be synced based on interval"""
        if system_name not in self.last_sync_times:
            return True
        
        last_sync = self.last_sync_times[system_name]
        interval = self.sync_intervals.get(system_name, timedelta(minutes=5))
        
        return datetime.now() - last_sync >= interval
    
    def _sync_system(self, system_name: str, client) -> Dict[str, Any]:
        """Sync individual system based on its capabilities"""
        sync_methods = {
            "cucm": self._sync_cucm,
            "cms": self._sync_cms,
            "meetingplace": self._sync_meetingplace,
            "uccx": self._sync_uccx,
            "expressway": self._sync_expressway,
            "sbc": self._sync_sbc,
            "tgw": self._sync_tgw
        }
        
        sync_method = sync_methods.get(system_name)
        if sync_method:
            return sync_method(client)
        else:
            logger.warning(f"No sync method for {system_name}")
            return {}
    
    def _sync_cucm(self, client: CUCMClient) -> Dict[str, Any]:
        """Sync CUCM data"""
        return {
            "devices": client.get_phones(),
            "users": client.get_users(),
            "status": client.get_status()
        }
    
    def _sync_cms(self, client: CMSClient) -> Dict[str, Any]:
        """Sync CMS data"""
        return {
            "meetings": client.get_meetings(),
            "active_calls": client.get_active_calls(),
            "status": client.get_status()
        }
    
    def _sync_meetingplace(self, client: MeetingPlaceClient) -> Dict[str, Any]:
        """Sync MeetingPlace data"""
        return {
            "meetings": client.get_meetings(),
            "status": client.get_status()
        }
    
    def _sync_uccx(self, client: UCCXClient) -> Dict[str, Any]:
        """Sync UCCX data"""
        return {
            "agents": client.get_agents(),
            "teams": client.get_teams(),
            "queues": client.get_queues(),
            "status": client.get_status()
        }
    
    def _sync_expressway(self, client: ExpresswayClient) -> Dict[str, Any]:
        """Sync Expressway data"""
        return {
            "registrations": client.get_registrations(),
            "calls": client.get_calls(),
            "users": client.get_users(),
            "status": client.get_status()
        }
    
    def _sync_sbc(self, client: SBCClient) -> Dict[str, Any]:
        """Sync SBC data"""
        return {
            "config_elements": client.get_config_elements("session-group"),
            "status": client.get_status(),
            "statistics": {
                "global_cps": client.global_cps,
                "global_sessions": client.global_con_sessions
            }
        }
    
    def _sync_tgw(self, client: TGWClient) -> Dict[str, Any]:
        """Sync TGW data"""
        return {
            "gateways": client.get_tgw_gateways(),
            "routes": client.get_tgw_routes(),
            "status": client.get_tgw_status()
        }
    
    def sync_system(self, system_name: str) -> Dict[str, Any]:
        """Sync a specific system"""
        if system_name not in self.clients:
            return {"status": "error", "error": f"System {system_name} not available"}
        
        client = self.clients[system_name]
        try:
            data = self._sync_system(system_name, client)
            self.last_sync_times[system_name] = datetime.now()
            
            return {
                "status": "success",
                "data": data,
                "sync_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync {system_name}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_system_status(self, system_name: str) -> Dict[str, Any]:
        """Get status of a specific system"""
        if system_name not in self.clients:
            return {"status": "error", "error": f"System {system_name} not available"}
        
        try:
            client = self.clients[system_name]
            return client.get_status()
        except Exception as e:
            logger.error(f"Failed to get status for {system_name}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_all_systems_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all systems"""
        status = {}
        
        for system_name, client in self.clients.items():
            try:
                status[system_name] = client.get_status()
            except Exception as e:
                status[system_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all client connections"""
        results = {}
        
        for system_name, client in self.clients.items():
            try:
                results[system_name] = client.test_connection()
            except Exception as e:
                logger.error(f"Connection test failed for {system_name}: {e}")
                results[system_name] = False
        
        return results
