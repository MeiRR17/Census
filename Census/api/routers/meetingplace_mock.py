"""
MeetingPlace Mock API Router
ניהול נתוני MeetingPlace מדומים
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Create FastAPI router
meetingplace_mock_router = APIRouter(
    prefix="/api/v1/meetingplace/mock",
    tags=["MeetingPlace Mock"],
    responses={404: {"description": "Not found"}}
)


# Pydantic Models for Request/Response
class MeetingPlaceMeetingCreate(BaseModel):
    """Model for creating a MeetingPlace meeting"""
    meeting_id: str
    subject: Optional[str] = "New Meeting"
    dialableMtgId: Optional[str] = None
    durationMin: Optional[int] = 0
    password: Optional[str] = None
    videoEnabled: Optional[bool] = True
    schedulerUserId: Optional[str] = "admin"


class MeetingPlaceUserCreate(BaseModel):
    """Model for creating a MeetingPlace user"""
    user_id: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    email: Optional[str] = None
    department: Optional[str] = ""
    phone_number: Optional[str] = ""


# Mock Data Store
class MeetingPlaceMockService:
    """שירות לניהול נתוני MeetingPlace מדומים"""
    
    def __init__(self):
        self.meetings = self._initialize_meetings()
        self.users = self._initialize_users()
    
    def _initialize_meetings(self) -> List[Dict[str, Any]]:
        """אתחול נתוני דמה של פגישות"""
        return [
            {
                "uniqueMeetingId": "mp-1001",
                "dialableMeetingId": "123456",
                "subject": "Daily Standup",
                "status": "active",
                "participantCount": 8,
                "schedulerUserId": "admin",
                "startTime": datetime.utcnow().isoformat() + "Z",
                "durationMin": 30,
                "videoEnabled": True,
                "hasPassword": False
            },
            {
                "uniqueMeetingId": "mp-1002",
                "dialableMeetingId": "234567",
                "subject": "Project Review",
                "status": "scheduled",
                "participantCount": 0,
                "schedulerUserId": "admin",
                "startTime": "2026-05-05T10:00:00Z",
                "durationMin": 60,
                "videoEnabled": True,
                "hasPassword": True,
                "password": "PROJ-2026"
            },
            {
                "uniqueMeetingId": "mp-1003",
                "dialableMeetingId": "345678",
                "subject": "Training Session",
                "status": "active",
                "participantCount": 15,
                "schedulerUserId": "trainer01",
                "startTime": datetime.utcnow().isoformat() + "Z",
                "durationMin": 120,
                "videoEnabled": True,
                "hasPassword": True,
                "password": "TRAIN-123"
            },
            {
                "uniqueMeetingId": "mp-1004",
                "dialableMeetingId": "456789",
                "subject": "Executive Briefing",
                "status": "ended",
                "participantCount": 0,
                "schedulerUserId": "execassistant",
                "startTime": "2026-05-03T14:00:00Z",
                "durationMin": 45,
                "videoEnabled": True,
                "hasPassword": True,
                "password": "EXEC-999"
            }
        ]
    
    def _initialize_users(self) -> List[Dict[str, Any]]:
        """אתחול נתוני דמה של משתמשים"""
        return [
            {
                "userId": "admin",
                "firstName": "Administrator",
                "lastName": "System",
                "email": "admin@company.com",
                "department": "IT",
                "status": "active",
                "canSchedule": True,
                "maxMeetings": 100
            },
            {
                "userId": "trainer01",
                "firstName": "John",
                "lastName": "Trainer",
                "email": "john.trainer@company.com",
                "department": "HR",
                "status": "active",
                "canSchedule": True,
                "maxMeetings": 50
            },
            {
                "userId": "execassistant",
                "firstName": "Sarah",
                "lastName": "Assistant",
                "email": "sarah.assistant@company.com",
                "department": "Executive",
                "status": "active",
                "canSchedule": True,
                "maxMeetings": 200
            },
            {
                "userId": "user001",
                "firstName": "David",
                "lastName": "Smith",
                "email": "david.smith@company.com",
                "department": "Sales",
                "status": "active",
                "canSchedule": True,
                "maxMeetings": 20
            }
        ]
    
    async def get_meetings(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """מחזיר את כל הפגישות, או מסנן לפי סטטוס"""
        meetings = self.meetings
        if status:
            meetings = [m for m in meetings if m["status"] == status]
        return meetings
    
    async def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """מחזיר פגישה בודדת לפי ID"""
        for meeting in self.meetings:
            if meeting["uniqueMeetingId"] == meeting_id or meeting["dialableMeetingId"] == meeting_id:
                return meeting
        return None
    
    async def create_meeting(self, meeting_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """יוצר פגישה חדשה"""
        new_meeting = {
            "uniqueMeetingId": f"mp-{len(self.meetings) + 1001}",
            "dialableMeetingId": meeting_data.get("meeting_id", f"{len(self.meetings) + 1001}00"),
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
        self.meetings.append(new_meeting)
        logger.info(f"Created new MeetingPlace meeting: {new_meeting['uniqueMeetingId']}")
        return new_meeting
    
    async def end_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """מסיים פגישה"""
        for meeting in self.meetings:
            if meeting["uniqueMeetingId"] == meeting_id:
                meeting["status"] = "ended"
                meeting["participantCount"] = 0
                return meeting
        return None
    
    async def delete_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """מוחק פגישה"""
        for i, meeting in enumerate(self.meetings):
            if meeting["uniqueMeetingId"] == meeting_id:
                self.meetings.pop(i)
                return {"deleted": True, "meeting_id": meeting_id}
        return {"deleted": False, "reason": "not_found"}
    
    async def get_users(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """מחזיר את כל המשתמשים, או מסנן לפי מחלקה"""
        users = self.users
        if department:
            users = [u for u in users if u["department"] == department]
        return users
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """מחזיר משתמש בודד לפי ID"""
        for user in self.users:
            if user["userId"] == user_id:
                return user
        return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """יוצר משתמש חדש"""
        new_user = {
            "userId": user_data.get("user_id"),
            "firstName": user_data.get("first_name", ""),
            "lastName": user_data.get("last_name", ""),
            "email": user_data.get("email", f"{user_data.get('user_id')}@company.com"),
            "department": user_data.get("department", ""),
            "status": "active",
            "canSchedule": True,
            "maxMeetings": 20
        }
        self.users.append(new_user)
        logger.info(f"Created new MeetingPlace user: {new_user['userId']}")
        return new_user
    
    def get_stats(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות"""
        return {
            "total_meetings": len(self.meetings),
            "active_meetings": len([m for m in self.meetings if m["status"] == "active"]),
            "scheduled_meetings": len([m for m in self.meetings if m["status"] == "scheduled"]),
            "ended_meetings": len([m for m in self.meetings if m["status"] == "ended"]),
            "total_users": len(self.users),
            "active_users": len([u for u in self.users if u["status"] == "active"]),
            "total_participants": sum(m["participantCount"] for m in self.meetings if m["status"] == "active")
        }


# Global singleton instance
meetingplace_mock_service = MeetingPlaceMockService()


# API Endpoints
@meetingplace_mock_router.get("/stats", response_model=Dict[str, Any])
async def get_meetingplace_stats():
    """
    Get MeetingPlace mock statistics
    
    Returns:
        MeetingPlace statistics
    """
    try:
        stats = meetingplace_mock_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get MeetingPlace stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.get("/meetings", response_model=List[Dict[str, Any]])
async def get_meetings(status: Optional[str] = None):
    """
    Get all MeetingPlace meetings, optionally filtered by status
    
    Args:
        status: Optional status filter (active, scheduled, ended)
        
    Returns:
        List of meetings
    """
    try:
        meetings = await meetingplace_mock_service.get_meetings(status=status)
        return meetings
    except Exception as e:
        logger.error(f"Failed to get meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.get("/meetings/{meeting_id}", response_model=Dict[str, Any])
async def get_meeting_by_id(meeting_id: str):
    """
    Get meeting by ID
    
    Args:
        meeting_id: Meeting unique ID or dialable ID
        
    Returns:
        Meeting details
    """
    try:
        meeting = await meetingplace_mock_service.get_meeting_by_id(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.post("/meetings", response_model=Dict[str, Any])
async def create_meeting(meeting_data: MeetingPlaceMeetingCreate):
    """
    Create a new MeetingPlace meeting
    
    Args:
        meeting_data: Meeting creation data
        
    Returns:
        Created meeting details
    """
    try:
        meeting = await meetingplace_mock_service.create_meeting(meeting_data.model_dump())
        if not meeting:
            raise HTTPException(status_code=400, detail="Invalid meeting data")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.post("/meetings/{meeting_id}/end", response_model=Dict[str, Any])
async def end_meeting(meeting_id: str):
    """
    End an active meeting
    
    Args:
        meeting_id: Meeting ID to end
        
    Returns:
        Ended meeting details
    """
    try:
        meeting = await meetingplace_mock_service.end_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """
    Delete a meeting
    
    Args:
        meeting_id: Meeting ID to delete
        
    Returns:
        Deletion result
    """
    try:
        result = await meetingplace_mock_service.delete_meeting(meeting_id)
        if not result["deleted"]:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(department: Optional[str] = None):
    """
    Get all MeetingPlace users, optionally filtered by department
    
    Args:
        department: Optional department filter
        
    Returns:
        List of users
    """
    try:
        users = await meetingplace_mock_service.get_users(department=department)
        return users
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(user_id: str):
    """
    Get user by ID
    
    Args:
        user_id: User ID
        
    Returns:
        User details
    """
    try:
        user = await meetingplace_mock_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_mock_router.post("/users", response_model=Dict[str, Any])
async def create_user(user_data: MeetingPlaceUserCreate):
    """
    Create a new MeetingPlace user
    
    Args:
        user_data: User creation data
        
    Returns:
        Created user details
    """
    try:
        user = await meetingplace_mock_service.create_user(user_data.model_dump())
        if not user:
            raise HTTPException(status_code=400, detail="Invalid user data")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
