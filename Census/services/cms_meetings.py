"""
CMS Mock Meetings Service
מדמה שרת CMS עם נתוני ועידות לפיתוח
"""

import asyncio
import random
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CMSMeeting:
    """מודל נתונים של ישיבת CMS"""
    id: str
    meeting_id: str
    name: str
    type: str  # audio, video, blast_dial
    group: str
    access_level: str
    status: str  # active, idle, scheduled, not_in_use
    participants_count: int
    duration: int  # minutes
    last_used_at: str
    password: str
    password_masked: str
    cms_node: str

class CMSMeetingsService:
    """שירות לניהול ועידות CMS מדומות"""
    
    def __init__(self):
        self.meetings = self._initialize_meetings()
    
    def _initialize_meetings(self) -> List[CMSMeeting]:
        """אתחול נתוני דמה של ועידות"""
        return [
            CMSMeeting(
                id="cms-1001",
                meeting_id="891245",
                name="Command Audio Bridge",
                type="audio",
                group="Operations",
                access_level="audio",
                status="active",
                participants_count=12,
                duration=34,
                last_used_at="2026-03-22T08:40:00Z",
                password="AUDIO-7781",
                password_masked="******",
                cms_node="CMS-DC-1"
            ),
            CMSMeeting(
                id="cms-1002",
                meeting_id="891246",
                name="Daily Ops Audio",
                type="audio",
                group="NOC",
                access_level="audio",
                status="idle",
                participants_count=0,
                duration=0,
                last_used_at="2026-04-05T16:20:00Z",
                password="AUDIO-3394",
                password_masked="******",
                cms_node="CMS-DC-2"
            ),
            CMSMeeting(
                id="cms-2001",
                meeting_id="771110",
                name="Leadership Video Room",
                type="video",
                group="Management",
                access_level="video",
                status="active",
                participants_count=7,
                duration=52,
                last_used_at="2026-04-05T09:05:00Z",
                password="VIDEO-2288",
                password_masked="******",
                cms_node="CMS-DC-1"
            ),
            CMSMeeting(
                id="cms-2002",
                meeting_id="771111",
                name="Training Video Hall",
                type="video",
                group="HR",
                access_level="video",
                status="scheduled",
                participants_count=0,
                duration=0,
                last_used_at="2026-04-05T12:35:00Z",
                password="VIDEO-9915",
                password_masked="******",
                cms_node="CMS-DC-3"
            ),
            CMSMeeting(
                id="cms-3001",
                meeting_id="551900",
                name="Mass Notification Dialout",
                type="blast_dial",
                group="Emergency",
                access_level="blast_dial",
                status="active",
                participants_count=24,
                duration=9,
                last_used_at="2026-04-05T07:55:00Z",
                password="BLAST-1044",
                password_masked="******",
                cms_node="CMS-DC-2"
            ),
            CMSMeeting(
                id="cms-3002",
                meeting_id="551901",
                name="Legacy Blast Group",
                type="blast_dial",
                group="NOT IN USE",
                access_level="blast_dial",
                status="not_in_use",
                participants_count=0,
                duration=0,
                last_used_at="2026-04-05T05:10:00Z",
                password="BLAST-0000",
                password_masked="******",
                cms_node="CMS-DC-3"
            )
        ]
    
    async def get_meetings(self, meeting_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """מחזיר את כל הישיבות"""
        meetings = self.meetings
        if meeting_type:
            meetings = [m for m in meetings if m.type == meeting_type]
        return [asdict(meeting) for meeting in meetings]
    
    async def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """מחזיר ישיבה בודדת"""
        for meeting in self.meetings:
            if meeting.meeting_id == meeting_id:
                return asdict(meeting)
        return None
    
    async def create_meeting(self, meeting_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """יוצר ישיבה חדשה"""
        meeting_id = str(meeting_data.get("meetingId", "")).strip()
        if not meeting_id:
            return None
        
        for meeting in self.meetings:
            if meeting.meeting_id == meeting_id:
                return asdict(meeting)
        
        meeting_type = meeting_data.get("type", "audio")
        password_prefix = {
            "video": "VIDEO",
            "blast_dial": "BLAST",
            "audio": "AUDIO"
        }.get(meeting_type, "AUDIO")
        
        random_suffix = random.randint(1000, 9999)
        password = f"{password_prefix}-{random_suffix}"
        
        max_id = 3000
        for meeting in self.meetings:
            try:
                numeric_id = int(meeting.id.replace("cms-", ""))
                max_id = max(max_id, numeric_id)
            except ValueError:
                continue
        
        new_meeting = CMSMeeting(
            id=f"cms-{max_id + 1}",
            meeting_id=meeting_id,
            name=meeting_data.get("name", f"Meeting {meeting_id}"),
            type=meeting_type,
            group=meeting_data.get("group", "Unassigned"),
            access_level=meeting_type,
            status="idle",
            participants_count=0,
            duration=0,
            last_used_at=datetime.utcnow().isoformat() + "Z",
            password=password,
            password_masked="******",
            cms_node=meeting_data.get("cmsNode", "CMS-LOCAL-1")
        )
        
        self.meetings.insert(0, new_meeting)
        return asdict(new_meeting)
    
    async def update_meeting_password(self, meeting_id: str, new_password: str) -> Optional[Dict[str, Any]]:
        """מעדכן סיסמת ישיבה"""
        for meeting in self.meetings:
            if meeting.meeting_id == meeting_id:
                meeting.password = new_password
                meeting.password_masked = "******" if new_password else "-"
                meeting.last_used_at = datetime.utcnow().isoformat() + "Z"
                return asdict(meeting)
        return None
    
    async def delete_meeting(self, meeting_id: str, actor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """מוחק ישיבה"""
        meeting_index = None
        for i, meeting in enumerate(self.meetings):
            if meeting.meeting_id == meeting_id:
                meeting_index = i
                break
        
        if meeting_index is None:
            return {"deleted": False, "reason": "not_found"}
        
        self.meetings.pop(meeting_index)
        return {"deleted": True, "reason": "ok"}
    
    def get_meeting_stats(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות"""
        total_meetings = len(self.meetings)
        active_meetings = len([m for m in self.meetings if m.status == "active"])
        total_participants = sum(m.participants_count for m in self.meetings)
        
        by_type = {}
        for meeting in self.meetings:
            by_type[meeting.type] = by_type.get(meeting.type, 0) + 1
        
        by_status = {}
        for meeting in self.meetings:
            by_status[meeting.status] = by_status.get(meeting.status, 0) + 1
        
        return {
            "total_meetings": total_meetings,
            "active_meetings": active_meetings,
            "total_participants": total_participants,
            "by_type": by_type,
            "by_status": by_status
        }

cms_meetings_service = CMSMeetingsService()
