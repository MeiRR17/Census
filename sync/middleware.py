"""
Sync Middleware - Handles bidirectional updates between Census and external systems
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging
from clients import (
    CUCMClient, CMSClient, MeetingPlaceClient, 
    UCCXClient, ExpresswayClient, SBCClient, TGWClient
)

logger = logging.getLogger(__name__)

class SyncMiddleware:
    """Middleware for bidirectional synchronization"""
    
    def __init__(self, config: Dict[str, Dict[str, str]], database):
        """
        Initialize sync middleware
        
        Args:
            config: System configurations
            database: Database connection
        """
        self.config = config
        self.database = database
        self.clients = {}
        self._initialize_clients()
        
        # Register update handlers
        self.update_handlers = {
            "devices": self._handle_device_update,
            "users": self._handle_user_update,
            "meetings": self._handle_meeting_update
        }
    
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
                    
                    if client.authenticate():
                        self.clients[system_name] = client
                        logger.info(f"Middleware connected to {system_name}")
                        
                except Exception as e:
                    logger.error(f"Middleware failed to connect to {system_name}: {e}")
    
    def handle_update(self, entity_type: str, entity_id: str, 
                     old_data: Dict[str, Any], new_data: Dict[str, Any],
                     source_system: str) -> Dict[str, Any]:
        """
        Handle update from Census and propagate to external systems
        
        Args:
            entity_type: Type of entity (devices, users, meetings)
            entity_id: ID of the entity
            old_data: Previous entity data
            new_data: New entity data
            source_system: System that originated the change
            
        Returns:
            Results of update propagation
        """
        logger.info(f"Handling {entity_type} update for {entity_id} from {source_system}")
        
        try:
            handler = self.update_handlers.get(entity_type)
            if not handler:
                logger.warning(f"No handler for entity type: {entity_type}")
                return {"status": "skipped", "reason": "No handler"}
            
            results = handler(entity_id, old_data, new_data, source_system)
            return results
            
        except Exception as e:
            logger.error(f"Failed to handle {entity_type} update: {e}")
            return {
                "status": "error",
                "error": str(e),
                "entity_type": entity_type,
                "entity_id": entity_id
            }
    
    def _handle_device_update(self, device_id: str, old_data: Dict[str, Any], 
                             new_data: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Handle device update and propagate to external systems"""
        results = {}
        
        # Determine which systems need updates
        target_systems = self._get_target_systems("devices", source_system)
        
        for system_name in target_systems:
            if system_name not in self.clients:
                continue
            
            try:
                client = self.clients[system_name]
                
                if system_name == "cucm":
                    result = self._update_cucm_device(client, device_id, old_data, new_data)
                elif system_name == "expressway":
                    result = self._update_expressway_device(client, device_id, old_data, new_data)
                else:
                    logger.warning(f"Device updates not supported for {system_name}")
                    result = {"status": "skipped", "reason": "Updates not supported"}
                
                results[system_name] = result
                
            except Exception as e:
                logger.error(f"Failed to update device in {system_name}: {e}")
                results[system_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def _handle_user_update(self, user_id: str, old_data: Dict[str, Any], 
                           new_data: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Handle user update and propagate to external systems"""
        results = {}
        
        target_systems = self._get_target_systems("users", source_system)
        
        for system_name in target_systems:
            if system_name not in self.clients:
                continue
            
            try:
                client = self.clients[system_name]
                
                if system_name == "cucm":
                    result = self._update_cucm_user(client, user_id, old_data, new_data)
                elif system_name == "uccx":
                    result = self._update_uccx_user(client, user_id, old_data, new_data)
                elif system_name == "expressway":
                    result = self._update_expressway_user(client, user_id, old_data, new_data)
                else:
                    logger.warning(f"User updates not supported for {system_name}")
                    result = {"status": "skipped", "reason": "Updates not supported"}
                
                results[system_name] = result
                
            except Exception as e:
                logger.error(f"Failed to update user in {system_name}: {e}")
                results[system_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def _handle_meeting_update(self, meeting_id: str, old_data: Dict[str, Any], 
                              new_data: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Handle meeting update and propagate to external systems"""
        results = {}
        
        target_systems = self._get_target_systems("meetings", source_system)
        
        for system_name in target_systems:
            if system_name not in self.clients:
                continue
            
            try:
                client = self.clients[system_name]
                
                if system_name == "cms":
                    result = self._update_cms_meeting(client, meeting_id, old_data, new_data)
                elif system_name == "meetingplace":
                    result = self._update_meetingplace_meeting(client, meeting_id, old_data, new_data)
                else:
                    logger.warning(f"Meeting updates not supported for {system_name}")
                    result = {"status": "skipped", "reason": "Updates not supported"}
                
                results[system_name] = result
                
            except Exception as e:
                logger.error(f"Failed to update meeting in {system_name}: {e}")
                results[system_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def _get_target_systems(self, entity_type: str, source_system: str) -> List[str]:
        """Get target systems for entity updates"""
        # Define which systems should receive updates for each entity type
        entity_targets = {
            "devices": ["cucm", "expressway"],
            "users": ["cucm", "uccx", "expressway"],
            "meetings": ["cms", "meetingplace"]
        }
        
        targets = entity_targets.get(entity_type, [])
        # Remove the source system to avoid update loops
        return [t for t in targets if t != source_system]
    
    def _update_cucm_device(self, client: CUCMClient, device_id: str, 
                           old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update device in CUCM"""
        try:
            # Map Census device data to CUCM format
            cucm_data = {
                "description": new_data.get("description", ""),
                "devicePool": new_data.get("device_pool", "Default"),
                "location": new_data.get("location", "Hub_None")
            }
            
            success = client.update_phone(device_id, cucm_data)
            
            return {
                "status": "success" if success else "failed",
                "device_id": device_id,
                "updated_fields": list(cucm_data.keys())
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _update_expressway_device(self, client: ExpresswayClient, device_id: str,
                                 old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update device in Expressway"""
        try:
            # Expressway typically doesn't allow device updates via API
            # This would be implemented based on actual Expressway capabilities
            logger.info(f"Expressway device update not implemented for {device_id}")
            return {"status": "skipped", "reason": "Expressway device updates not supported"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _update_cucm_user(self, client: CUCMClient, user_id: str,
                         old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user in CUCM"""
        try:
            # CUCM user updates would be implemented via AXL
            # This is a placeholder implementation
            logger.info(f"CUCM user update not fully implemented for {user_id}")
            return {"status": "skipped", "reason": "CUCM user updates not fully implemented"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _update_uccx_user(self, client: UCCXClient, user_id: str,
                         old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user in UCCX"""
        try:
            # Map Census user data to UCCX format
            uccx_data = {
                "firstName": new_data.get("first_name", ""),
                "lastName": new_data.get("last_name", ""),
                "extension": new_data.get("phone", "")
            }
            
            success = client.update_agent(user_id, uccx_data)
            
            return {
                "status": "success" if success else "failed",
                "user_id": user_id,
                "updated_fields": list(uccx_data.keys())
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _update_expressway_user(self, client: ExpresswayClient, user_id: str,
                               old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user in Expressway"""
        try:
            # Map Census user data to Expressway format
            expressway_data = {
                "name": new_data.get("name", ""),
                "email": new_data.get("email", ""),
                "department": new_data.get("department", "")
            }
            
            success = client.update_user(user_id, expressway_data)
            
            return {
                "status": "success" if success else "failed",
                "user_id": user_id,
                "updated_fields": list(expressway_data.keys())
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _update_cms_meeting(self, client: CMSClient, meeting_id: str,
                           old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update meeting in CMS"""
        try:
            # Map Census meeting data to CMS format
            cms_data = {
                "name": new_data.get("name", ""),
                "passcode": new_data.get("passcode", "")
            }
            
            success = client.update_meeting(meeting_id, cms_data)
            
            return {
                "status": "success" if success else "failed",
                "meeting_id": meeting_id,
                "updated_fields": list(cms_data.keys())
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _update_meetingplace_meeting(self, client: MeetingPlaceClient, meeting_id: str,
                                    old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update meeting in MeetingPlace"""
        try:
            # MeetingPlace updates would be implemented via SOAP API
            logger.info(f"MeetingPlace meeting update not fully implemented for {meeting_id}")
            return {"status": "skipped", "reason": "MeetingPlace updates not fully implemented"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def create_entity(self, entity_type: str, entity_data: Dict[str, Any],
                      target_systems: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create entity in external systems
        
        Args:
            entity_type: Type of entity (devices, users, meetings)
            entity_data: Entity data
            target_systems: Specific target systems (optional)
        """
        logger.info(f"Creating {entity_type} in external systems")
        
        results = {}
        
        if target_systems is None:
            target_systems = self._get_target_systems(entity_type, "census")
        
        for system_name in target_systems:
            if system_name not in self.clients:
                continue
            
            try:
                client = self.clients[system_name]
                
                if entity_type == "devices":
                    result = self._create_device_in_system(client, system_name, entity_data)
                elif entity_type == "users":
                    result = self._create_user_in_system(client, system_name, entity_data)
                elif entity_type == "meetings":
                    result = self._create_meeting_in_system(client, system_name, entity_data)
                else:
                    result = {"status": "skipped", "reason": "Unsupported entity type"}
                
                results[system_name] = result
                
            except Exception as e:
                logger.error(f"Failed to create {entity_type} in {system_name}: {e}")
                results[system_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def _create_device_in_system(self, client, system_name: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create device in specific system"""
        if system_name == "cucm":
            success = client.add_phone(device_data)
            return {
                "status": "success" if success else "failed",
                "device_name": device_data.get("name")
            }
        else:
            return {"status": "skipped", "reason": f"Device creation not supported for {system_name}"}
    
    def _create_user_in_system(self, client, system_name: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user in specific system"""
        if system_name == "uccx":
            uccx_data = {
                "agentId": user_data.get("user_id"),
                "firstName": user_data.get("first_name", ""),
                "lastName": user_data.get("last_name", ""),
                "extension": user_data.get("phone", "")
            }
            success = client.create_agent(uccx_data)
            return {
                "status": "success" if success else "failed",
                "user_id": user_data.get("user_id")
            }
        elif system_name == "expressway":
            expressway_data = {
                "username": user_data.get("user_id"),
                "name": user_data.get("name", ""),
                "email": user_data.get("email", "")
            }
            success = client.create_user(expressway_data)
            return {
                "status": "success" if success else "failed",
                "user_id": user_data.get("user_id")
            }
        else:
            return {"status": "skipped", "reason": f"User creation not supported for {system_name}"}
    
    def _create_meeting_in_system(self, client, system_name: str, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create meeting in specific system"""
        if system_name == "cms":
            success = client.create_meeting(meeting_data)
            return {
                "status": "success" if success else "failed",
                "meeting_id": meeting_data.get("meeting_id")
            }
        elif system_name == "meetingplace":
            success = client.create_meeting(meeting_data)
            return {
                "status": "success" if success else "failed",
                "meeting_id": meeting_data.get("meeting_id")
            }
        else:
            return {"status": "skipped", "reason": f"Meeting creation not supported for {system_name}"}
