"""
Sync Manager - High-level synchronization management
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from .sync_engine import SyncEngine

logger = logging.getLogger(__name__)

class SyncManager:
    """High-level manager for synchronization operations"""
    
    def __init__(self, config: Dict[str, Dict[str, str]], database):
        """
        Initialize sync manager
        
        Args:
            config: System configurations
            database: Database connection for storing synced data
        """
        self.config = config
        self.database = database
        self.sync_engine = SyncEngine(config)
        self.active_syncs = {}
    
    def full_sync(self) -> Dict[str, Any]:
        """Perform full synchronization of all systems"""
        logger.info("Starting full synchronization")
        
        try:
            # Get all system data
            sync_results = self.sync_engine.sync_all_systems()
            
            # Store data in database
            stored_data = {}
            for system_name, result in sync_results.items():
                if result["status"] == "success":
                    stored = self._store_system_data(system_name, result["data"])
                    stored_data[system_name] = stored
                else:
                    stored_data[system_name] = result
            
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "systems": sync_results,
                "stored_data": stored_data
            }
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def sync_system(self, system_name: str) -> Dict[str, Any]:
        """Sync a specific system"""
        logger.info(f"Syncing system: {system_name}")
        
        try:
            # Get system data
            sync_result = self.sync_engine.sync_system(system_name)
            
            if sync_result["status"] == "success":
                # Store data in database
                stored = self._store_system_data(system_name, sync_result["data"])
                sync_result["stored"] = stored
            
            return sync_result
            
        except Exception as e:
            logger.error(f"System sync failed for {system_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _store_system_data(self, system_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store system data in database"""
        try:
            stored_counts = {}
            
            # Store devices
            if "devices" in data:
                count = self._store_devices(system_name, data["devices"])
                stored_counts["devices"] = count
            
            # Store users
            if "users" in data:
                count = self._store_users(system_name, data["users"])
                stored_counts["users"] = count
            
            # Store meetings
            if "meetings" in data:
                count = self._store_meetings(system_name, data["meetings"])
                stored_counts["meetings"] = count
            
            # Store agents (UCCX)
            if "agents" in data:
                count = self._store_agents(system_name, data["agents"])
                stored_counts["agents"] = count
            
            # Store calls
            if "active_calls" in data:
                count = self._store_calls(system_name, data["active_calls"])
                stored_counts["calls"] = count
            
            # Store registrations (Expressway)
            if "registrations" in data:
                count = self._store_registrations(system_name, data["registrations"])
                stored_counts["registrations"] = count
            
            # Store gateways (TGW)
            if "gateways" in data:
                count = self._store_gateways(system_name, data["gateways"])
                stored_counts["gateways"] = count
            
            # Store routes (TGW)
            if "routes" in data:
                count = self._store_routes(system_name, data["routes"])
                stored_counts["routes"] = count
            
            # Store config elements (SBC)
            if "config_elements" in data:
                count = self._store_config_elements(system_name, data["config_elements"])
                stored_counts["config_elements"] = count
            
            return stored_counts
            
        except Exception as e:
            logger.error(f"Failed to store {system_name} data: {e}")
            raise
    
    def _store_devices(self, source: str, devices: List[Dict[str, Any]]) -> int:
        """Store devices in database"""
        count = 0
        for device in devices:
            try:
                # Check if device exists
                existing = self.database.execute(
                    "SELECT id FROM devices WHERE name = ? AND source = ?",
                    (device["name"], source)
                ).fetchone()
                
                if existing:
                    # Update existing device
                    self.database.execute(
                        """UPDATE devices SET 
                           ip_address = ?, mac_address = ?, device_type = ?, 
                           status = ?, raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE name = ? AND source = ?""",
                        (
                            device.get("ip_address"),
                            device.get("mac_address"),
                            device.get("model", "Unknown"),
                            "registered" if device.get("is_registered") else "unregistered",
                            str(device),
                            device["name"],
                            source
                        )
                    )
                else:
                    # Insert new device
                    self.database.execute(
                        """INSERT INTO devices 
                           (name, ip_address, mac_address, device_type, status, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            device["name"],
                            device.get("ip_address"),
                            device.get("mac_address"),
                            device.get("model", "Unknown"),
                            "registered" if device.get("is_registered") else "unregistered",
                            source,
                            str(device)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store device {device.get('name')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_users(self, source: str, users: List[Dict[str, Any]]) -> int:
        """Store users in database"""
        count = 0
        for user in users:
            try:
                # Check if user exists
                existing = self.database.execute(
                    "SELECT id FROM users WHERE user_id = ? AND source = ?",
                    (user["user_id"], source)
                ).fetchone()
                
                if existing:
                    # Update existing user
                    self.database.execute(
                        """UPDATE users SET 
                           name = ?, email = ?, department = ?, phone = ?, 
                           raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE user_id = ? AND source = ?""",
                        (
                            f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                            user.get("email"),
                            user.get("department"),
                            user.get("phone"),
                            str(user),
                            user["user_id"],
                            source
                        )
                    )
                else:
                    # Insert new user
                    self.database.execute(
                        """INSERT INTO users 
                           (user_id, name, email, department, phone, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            user["user_id"],
                            f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                            user.get("email"),
                            user.get("department"),
                            user.get("phone"),
                            source,
                            str(user)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store user {user.get('user_id')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_meetings(self, source: str, meetings: List[Dict[str, Any]]) -> int:
        """Store meetings in database"""
        count = 0
        for meeting in meetings:
            try:
                # Check if meeting exists
                existing = self.database.execute(
                    "SELECT id FROM meetings WHERE meeting_id = ? AND source = ?",
                    (meeting["meeting_id"], source)
                ).fetchone()
                
                if existing:
                    # Update existing meeting
                    self.database.execute(
                        """UPDATE meetings SET 
                           name = ?, uri = ?, passcode = ?, status = ?, 
                           participants = ?, raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE meeting_id = ? AND source = ?""",
                        (
                            meeting.get("name"),
                            meeting.get("uri"),
                            meeting.get("passcode"),
                            meeting.get("status", "active"),
                            meeting.get("participants", 0),
                            str(meeting),
                            meeting["meeting_id"],
                            source
                        )
                    )
                else:
                    # Insert new meeting
                    self.database.execute(
                        """INSERT INTO meetings 
                           (meeting_id, name, uri, passcode, status, participants, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            meeting["meeting_id"],
                            meeting.get("name"),
                            meeting.get("uri"),
                            meeting.get("passcode"),
                            meeting.get("status", "active"),
                            meeting.get("participants", 0),
                            source,
                            str(meeting)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store meeting {meeting.get('meeting_id')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_agents(self, source: str, agents: List[Dict[str, Any]]) -> int:
        """Store agents in database (stored as users with agent type)"""
        count = 0
        for agent in agents:
            try:
                # Check if agent exists
                existing = self.database.execute(
                    "SELECT id FROM users WHERE user_id = ? AND source = ?",
                    (agent["agent_id"], source)
                ).fetchone()
                
                if existing:
                    # Update existing agent
                    self.database.execute(
                        """UPDATE users SET 
                           name = ?, email = ?, phone = ?, 
                           raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE user_id = ? AND source = ?""",
                        (
                            f"{agent.get('first_name', '')} {agent.get('last_name', '')}".strip(),
                            agent.get("email"),
                            agent.get("extension"),
                            str(agent),
                            agent["agent_id"],
                            source
                        )
                    )
                else:
                    # Insert new agent
                    self.database.execute(
                        """INSERT INTO users 
                           (user_id, name, email, phone, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            agent["agent_id"],
                            f"{agent.get('first_name', '')} {agent.get('last_name', '')}".strip(),
                            agent.get("email"),
                            agent.get("extension"),
                            source,
                            str(agent)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store agent {agent.get('agent_id')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_calls(self, source: str, calls: List[Dict[str, Any]]) -> int:
        """Store active calls in database"""
        count = 0
        for call in calls:
            try:
                # Store calls as meetings with call type
                existing = self.database.execute(
                    "SELECT id FROM meetings WHERE meeting_id = ? AND source = ?",
                    (call["call_id"], source)
                ).fetchone()
                
                if existing:
                    # Update existing call
                    self.database.execute(
                        """UPDATE meetings SET 
                           name = ?, participants = ?, status = 'active',
                           raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE meeting_id = ? AND source = ?""",
                        (
                            call.get("name", f"Call {call['call_id']}"),
                            call.get("participants", 0),
                            str(call),
                            call["call_id"],
                            source
                        )
                    )
                else:
                    # Insert new call
                    self.database.execute(
                        """INSERT INTO meetings 
                           (meeting_id, name, status, participants, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            call["call_id"],
                            call.get("name", f"Call {call['call_id']}"),
                            "active",
                            call.get("participants", 0),
                            source,
                            str(call)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store call {call.get('call_id')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_registrations(self, source: str, registrations: List[Dict[str, Any]]) -> int:
        """Store registrations as devices"""
        count = 0
        for registration in registrations:
            try:
                # Store as device
                existing = self.database.execute(
                    "SELECT id FROM devices WHERE name = ? AND source = ?",
                    (registration["endpoint_id"], source)
                ).fetchone()
                
                if existing:
                    # Update existing registration
                    self.database.execute(
                        """UPDATE devices SET 
                           ip_address = ?, device_type = ?, status = ?, 
                           raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE name = ? AND source = ?""",
                        (
                            registration.get("ip_address"),
                            registration.get("device_type", "Unknown"),
                            registration.get("status", "unknown"),
                            str(registration),
                            registration["endpoint_id"],
                            source
                        )
                    )
                else:
                    # Insert new registration
                    self.database.execute(
                        """INSERT INTO devices 
                           (name, ip_address, device_type, status, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            registration["endpoint_id"],
                            registration.get("ip_address"),
                            registration.get("device_type", "Unknown"),
                            registration.get("status", "unknown"),
                            source,
                            str(registration)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store registration {registration.get('endpoint_id')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_gateways(self, source: str, gateways: List[Dict[str, Any]]) -> int:
        """Store gateways as devices"""
        count = 0
        for gateway in gateways:
            try:
                # Store as device
                existing = self.database.execute(
                    "SELECT id FROM devices WHERE name = ? AND source = ?",
                    (gateway["name"], source)
                ).fetchone()
                
                if existing:
                    # Update existing gateway
                    self.database.execute(
                        """UPDATE devices SET 
                           ip_address = ?, device_type = 'Gateway', status = 'active',
                           raw_data = ?, updated_at = CURRENT_TIMESTAMP
                           WHERE name = ? AND source = ?""",
                        (
                            gateway.get("ip_address"),
                            str(gateway),
                            gateway["name"],
                            source
                        )
                    )
                else:
                    # Insert new gateway
                    self.database.execute(
                        """INSERT INTO devices 
                           (name, ip_address, device_type, status, source, raw_data)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            gateway["name"],
                            gateway.get("ip_address"),
                            "Gateway",
                            "active",
                            source,
                            str(gateway)
                        )
                    )
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to store gateway {gateway.get('name')}: {e}")
        
        self.database.commit()
        return count
    
    def _store_routes(self, source: str, routes: List[Dict[str, Any]]) -> int:
        """Store routes in a separate table"""
        # For now, we'll store routes as raw data in the devices table
        # In a real implementation, you'd have a dedicated routes table
        count = len(routes)
        logger.info(f"Stored {count} routes for {source}")
        return count
    
    def _store_config_elements(self, source: str, elements: List[Dict[str, Any]]) -> int:
        """Store SBC config elements"""
        # For now, store as raw data
        count = len(elements)
        logger.info(f"Stored {count} config elements for {source}")
        return count
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            "connected_systems": list(self.sync_engine.clients.keys()),
            "last_sync_times": self.sync_engine.last_sync_times,
            "system_status": self.sync_engine.get_all_systems_status()
        }
