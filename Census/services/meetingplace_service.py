"""
MeetingPlace Service - Real Integration with MeetingPlace Server
שכבת שירות אמיתית לחיבור לשרת MeetingPlace דרך ה-SDK
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from ciscoaxl.meetingplace.client import MeetingPlaceClient, MeetingPlaceZeeper, get_meetingplace_zeeper
from ciscoaxl.meetingplace.config import MeetingPlaceConfig
from ciscoaxl.meetingplace import meetings, users

logger = logging.getLogger(__name__)


class MeetingPlaceService:
    """
    שירות אמיתי לניהול MeetingPlace
    משתמש ב-SDK של ciscoaxl לחיבור לשרת האמיתי
    """
    
    def __init__(self, config_file: str = "api/conf_reader/meeting_place_config.ini"):
        self.config = MeetingPlaceConfig(config_file)
        self.client: Optional[MeetingPlaceClient] = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the MeetingPlace client from configuration"""
        try:
            # Get first server configuration
            servers = self.config.get_servers()
            if not servers:
                logger.error("No MeetingPlace servers configured")
                return
            
            # Use first server
            server_name = list(servers.keys())[0]
            server_config = servers[server_name]
            
            self.client = MeetingPlaceClient(
                name=server_name,
                ip=server_config.get("ip"),
                username=server_config.get("username"),
                password=server_config.get("password")
            )
            logger.info(f"MeetingPlace client initialized for server: {server_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MeetingPlace client: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.client is not None
    
    async def get_meetings(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all meetings from MeetingPlace server
        
        Args:
            status: Optional filter by status (active, scheduled, ended)
            
        Returns:
            List of meetings
        """
        if not self.is_connected():
            logger.error("MeetingPlace client not connected")
            return []
        
        try:
            # Use SDK to get meetings
            meeting_list = meetings.get_all_meetings(self.client)
            
            # Transform to standard format
            result = []
            for mtg in meeting_list:
                meeting_data = {
                    "uniqueMeetingId": mtg.get("mtgId", ""),
                    "dialableMeetingId": mtg.get("dialableMtgId", ""),
                    "subject": mtg.get("subject", ""),
                    "status": self._map_status(mtg.get("status", "")),
                    "participantCount": mtg.get("participantCount", 0),
                    "schedulerUserId": mtg.get("schedulerUserId", ""),
                    "startTime": mtg.get("startTime", ""),
                    "durationMin": mtg.get("durationMin", 0),
                    "videoEnabled": mtg.get("videoEnabled", True),
                    "hasPassword": bool(mtg.get("password")),
                    "password": mtg.get("password", "")
                }
                
                # Apply status filter if specified
                if status and meeting_data["status"] != status:
                    continue
                    
                result.append(meeting_data)
            
            logger.info(f"Retrieved {len(result)} meetings from MeetingPlace")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get meetings from MeetingPlace: {e}")
            return []
    
    async def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting by ID"""
        if not self.is_connected():
            return None
        
        try:
            meeting = meetings.get_meeting(self.client, meeting_id)
            if meeting:
                return {
                    "uniqueMeetingId": meeting.get("mtgId", ""),
                    "dialableMeetingId": meeting.get("dialableMtgId", ""),
                    "subject": meeting.get("subject", ""),
                    "status": self._map_status(meeting.get("status", "")),
                    "participantCount": meeting.get("participantCount", 0),
                    "schedulerUserId": meeting.get("schedulerUserId", ""),
                    "startTime": meeting.get("startTime", ""),
                    "durationMin": meeting.get("durationMin", 0),
                    "videoEnabled": meeting.get("videoEnabled", True),
                    "hasPassword": bool(meeting.get("password")),
                    "password": meeting.get("password", "")
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get meeting {meeting_id}: {e}")
            return None
    
    async def create_meeting(self, meeting_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new meeting on MeetingPlace server
        
        Args:
            meeting_data: Meeting creation parameters
            
        Returns:
            Created meeting details
        """
        if not self.is_connected():
            logger.error("MeetingPlace client not connected")
            return None
        
        try:
            # Use SDK to create meeting
            success = meetings.create_scheduled_meeting(
                self.client,
                meeting_id=meeting_data.get("meeting_id"),
                password=meeting_data.get("password")
            )
            
            if success:
                logger.info(f"Created meeting: {meeting_data.get('meeting_id')}")
                # Return the created meeting data
                return {
                    "uniqueMeetingId": f"mp-{meeting_data.get('meeting_id')}",
                    "dialableMeetingId": meeting_data.get("meeting_id"),
                    "subject": meeting_data.get("subject", "New Meeting"),
                    "status": "scheduled",
                    "participantCount": 0,
                    "schedulerUserId": meeting_data.get("schedulerUserId", "admin"),
                    "startTime": datetime.utcnow().isoformat() + "Z",
                    "durationMin": meeting_data.get("durationMin", 60),
                    "videoEnabled": meeting_data.get("videoEnabled", True),
                    "hasPassword": bool(meeting_data.get("password")),
                    "password": meeting_data.get("password", "")
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to create meeting: {e}")
            return None
    
    async def end_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """End an active meeting"""
        if not self.is_connected():
            return None
        
        try:
            success = meetings.end_meeting(self.client, meeting_id)
            if success:
                logger.info(f"Ended meeting: {meeting_id}")
                return {"ended": True, "meeting_id": meeting_id}
            return None
            
        except Exception as e:
            logger.error(f"Failed to end meeting {meeting_id}: {e}")
            return None
    
    async def delete_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Delete a meeting"""
        if not self.is_connected():
            return {"deleted": False, "reason": "not_connected"}
        
        try:
            success = meetings.delete_meeting(self.client, meeting_id)
            if success:
                logger.info(f"Deleted meeting: {meeting_id}")
                return {"deleted": True, "meeting_id": meeting_id}
            return {"deleted": False, "reason": "failed"}
            
        except Exception as e:
            logger.error(f"Failed to delete meeting {meeting_id}: {e}")
            return {"deleted": False, "reason": str(e)}
    
    async def get_users(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all users from MeetingPlace"""
        if not self.is_connected():
            logger.error("MeetingPlace client not connected")
            return []
        
        try:
            user_list = users.get_all_users(self.client)
            
            result = []
            for user in user_list:
                user_data = {
                    "userId": user.get("userId", ""),
                    "firstName": user.get("firstName", ""),
                    "lastName": user.get("lastName", ""),
                    "email": user.get("email", ""),
                    "department": user.get("department", ""),
                    "status": "active" if user.get("enabled") else "inactive",
                    "canSchedule": user.get("canSchedule", False),
                    "maxMeetings": user.get("maxMeetings", 20)
                }
                
                # Apply department filter if specified
                if department and user_data["department"] != department:
                    continue
                    
                result.append(user_data)
            
            logger.info(f"Retrieved {len(result)} users from MeetingPlace")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get users from MeetingPlace: {e}")
            return []
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not self.is_connected():
            return None
        
        try:
            user = users.get_user(self.client, user_id)
            if user:
                return {
                    "userId": user.get("userId", ""),
                    "firstName": user.get("firstName", ""),
                    "lastName": user.get("lastName", ""),
                    "email": user.get("email", ""),
                    "department": user.get("department", ""),
                    "status": "active" if user.get("enabled") else "inactive",
                    "canSchedule": user.get("canSchedule", False),
                    "maxMeetings": user.get("maxMeetings", 20)
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user on MeetingPlace"""
        if not self.is_connected():
            logger.error("MeetingPlace client not connected")
            return None
        
        try:
            success = users.create_user(
                self.client,
                user_id=user_data.get("user_id"),
                user_fields={
                    "firstName": user_data.get("first_name", ""),
                    "lastName": user_data.get("last_name", ""),
                    "email": user_data.get("email", ""),
                    "department": user_data.get("department", "")
                }
            )
            
            if success:
                logger.info(f"Created user: {user_data.get('user_id')}")
                return {
                    "userId": user_data.get("user_id"),
                    "firstName": user_data.get("first_name", ""),
                    "lastName": user_data.get("last_name", ""),
                    "email": user_data.get("email", f"{user_data.get('user_id')}@company.com"),
                    "department": user_data.get("department", ""),
                    "status": "active",
                    "canSchedule": True,
                    "maxMeetings": 20
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from MeetingPlace"""
        if not self.is_connected():
            return {
                "total_meetings": 0,
                "active_meetings": 0,
                "scheduled_meetings": 0,
                "ended_meetings": 0,
                "total_users": 0,
                "active_users": 0,
                "total_participants": 0,
                "connected": False
            }
        
        try:
            # This would need to be implemented based on actual MeetingPlace API
            # For now, return basic connection status
            return {
                "connected": True,
                "total_meetings": 0,  # Would need to count from get_meetings
                "total_users": 0,      # Would need to count from get_users
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _map_status(self, mp_status: str) -> str:
        """Map MeetingPlace status to our standard status"""
        status_map = {
            "active": "active",
            "scheduled": "scheduled", 
            "completed": "ended",
            "cancelled": "ended",
            "inProgress": "active"
        }
        return status_map.get(mp_status, "unknown")


# Global instance
meetingplace_service = MeetingPlaceService()
