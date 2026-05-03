"""
CUCM Mock Service
מדמה שרת CUCM עם נתוני דמה לפיתוח
"""

import asyncio
import random
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CUCMPhone:
    """מודל נתונים של טלפון CUCM"""
    id: str
    name: str
    description: str
    model: str
    mac_address: str
    ip_address: str
    status: str  # registered, unregistered, rejected
    device_pool: str
    calling_search_space: str
    line_dn: str
    line_partition: str
    last_registered: str

@dataclass
class CUCMUser:
    """מודל נתונים של משתמש CUCM"""
    user_id: str
    first_name: str
    last_name: str
    user_id_field: str
    department: str
    email: str
    phone_number: str
    status: str  # active, inactive
    associated_devices: List[str]
    primary_extension: str

@dataclass
class CUCMLine:
    """מודל נתונים של קו טלפון CUCM"""
    pattern: str
    description: str
    partition: str
    calling_search_space: str
    route_partition: str
    status: str  # active, inactive
    usage: str  # device, voicemail, hunt pilot

class CUCMMockService:
    """שירות לניהול נתוני CUCM מדומים"""
    
    def __init__(self):
        self.phones = self._initialize_phones()
        self.users = self._initialize_users()
        self.lines = self._initialize_lines()
    
    def _initialize_phones(self) -> List[CUCMPhone]:
        """אתחול נתוני דמה של טלפונים"""
        return [
            CUCMPhone(
                id="SEP001122334455",
                name="SEPD001122334455",
                description="Executive Phone - CEO Office",
                model="Cisco 8851",
                mac_address="00:11:22:33:44:55",
                ip_address="10.1.1.100",
                status="registered",
                device_pool="Default",
                calling_search_space="CSS-Internal",
                line_dn="1001",
                line_partition="PT-Internal",
                last_registered="2026-04-30T08:00:00Z"
            ),
            CUCMPhone(
                id="SEP001122334456",
                name="SEPD001122334456",
                description="Manager Phone - Sales Office",
                model="Cisco 7841",
                mac_address="00:11:22:33:44:56",
                ip_address="10.1.1.101",
                status="registered",
                device_pool="Sales-Pool",
                calling_search_space="CSS-Sales",
                line_dn="2001",
                line_partition="PT-Sales",
                last_registered="2026-04-30T08:15:00Z"
            ),
            CUCMPhone(
                id="SEP001122334457",
                name="SEPD001122334457",
                description="Reception Phone - Main Lobby",
                model="Cisco 8865",
                mac_address="00:11:22:33:44:57",
                ip_address="10.1.1.102",
                status="registered",
                device_pool="Reception-Pool",
                calling_search_space="CSS-Reception",
                line_dn="3001",
                line_partition="PT-Reception",
                last_registered="2026-04-30T07:45:00Z"
            ),
            CUCMPhone(
                id="SEP001122334458",
                name="SEPD001122334458",
                description="Conference Room Phone - Boardroom",
                model="Cisco 8865",
                mac_address="00:11:22:33:44:58",
                ip_address="10.1.1.103",
                status="unregistered",
                device_pool="Conference-Pool",
                calling_search_space="CSS-Internal",
                line_dn="4001",
                line_partition="PT-Internal",
                last_registered="2026-04-29T17:00:00Z"
            ),
            CUCMPhone(
                id="SEP001122334459",
                name="SEPD001122334459",
                description="IT Support Phone - Help Desk",
                model="Cisco 7841",
                mac_address="00:11:22:33:44:59",
                ip_address="10.1.1.104",
                status="registered",
                device_pool="IT-Pool",
                calling_search_space="CSS-IT",
                line_dn="5001",
                line_partition="PT-IT",
                last_registered="2026-04-30T08:30:00Z"
            ),
            CUCMPhone(
                id="SEP001122334460",
                name="SEPD001122334460",
                description="Warehouse Phone - Loading Dock",
                model="Cisco 7821",
                mac_address="00:11:22:33:44:60",
                ip_address="10.1.1.105",
                status="registered",
                device_pool="Warehouse-Pool",
                calling_search_space="CSS-Warehouse",
                line_dn="6001",
                line_partition="PT-Warehouse",
                last_registered="2026-04-30T06:00:00Z"
            )
        ]
    
    def _initialize_users(self) -> List[CUCMUser]:
        """אתחול נתוני דמה של משתמשים"""
        return [
            CUCMUser(
                user_id="user001",
                first_name="John",
                last_name="Smith",
                user_id_field="jsmith",
                department="Executive",
                email="john.smith@company.com",
                phone_number="1001",
                status="active",
                associated_devices=["SEP001122334455"],
                primary_extension="1001"
            ),
            CUCMUser(
                user_id="user002",
                first_name="Sarah",
                last_name="Johnson",
                user_id_field="sjohnson",
                department="Sales",
                email="sarah.johnson@company.com",
                phone_number="2001",
                status="active",
                associated_devices=["SEP001122334456"],
                primary_extension="2001"
            ),
            CUCMUser(
                user_id="user003",
                first_name="Mike",
                last_name="Williams",
                user_id_field="mwilliams",
                department="Reception",
                email="mike.williams@company.com",
                phone_number="3001",
                status="active",
                associated_devices=["SEP001122334457"],
                primary_extension="3001"
            ),
            CUCMUser(
                user_id="user004",
                first_name="Emily",
                last_name="Brown",
                user_id_field="ebrown",
                department="IT",
                email="emily.brown@company.com",
                phone_number="5001",
                status="active",
                associated_devices=["SEP001122334459"],
                primary_extension="5001"
            ),
            CUCMUser(
                user_id="user005",
                first_name="David",
                last_name="Davis",
                user_id_field="ddavis",
                department="Warehouse",
                email="david.davis@company.com",
                phone_number="6001",
                status="active",
                associated_devices=["SEP001122334460"],
                primary_extension="6001"
            )
        ]
    
    def _initialize_lines(self) -> List[CUCMLine]:
        """אתחול נתוני דמה של קווים"""
        return [
            CUCMLine(
                pattern="1001",
                description="CEO Line",
                partition="PT-Internal",
                calling_search_space="CSS-Internal",
                route_partition="PT-Internal",
                status="active",
                usage="device"
            ),
            CUCMLine(
                pattern="2001",
                description="Sales Manager Line",
                partition="PT-Sales",
                calling_search_space="CSS-Sales",
                route_partition="PT-Sales",
                status="active",
                usage="device"
            ),
            CUCMLine(
                pattern="3001",
                description="Reception Line",
                partition="PT-Reception",
                calling_search_space="CSS-Reception",
                route_partition="PT-Reception",
                status="active",
                usage="device"
            ),
            CUCMLine(
                pattern="4001",
                description="Conference Room Line",
                partition="PT-Internal",
                calling_search_space="CSS-Internal",
                route_partition="PT-Internal",
                status="inactive",
                usage="device"
            ),
            CUCMLine(
                pattern="5001",
                description="IT Support Line",
                partition="PT-IT",
                calling_search_space="CSS-IT",
                route_partition="PT-IT",
                status="active",
                usage="device"
            ),
            CUCMLine(
                pattern="6001",
                description="Warehouse Line",
                partition="PT-Warehouse",
                calling_search_space="CSS-Warehouse",
                route_partition="PT-Warehouse",
                status="active",
                usage="device"
            ),
            CUCMLine(
                pattern="8000",
                description="Main Voicemail",
                partition="PT-Voicemail",
                calling_search_space="CSS-All",
                route_partition="PT-Voicemail",
                status="active",
                usage="voicemail"
            )
        ]
    
    async def get_phones(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """מחזיר את כל הטלפונים, או מסנן לפי סטטוס"""
        phones = self.phones
        if status:
            phones = [p for p in phones if p.status == status]
        return [asdict(phone) for phone in phones]
    
    async def get_phone_by_id(self, phone_id: str) -> Optional[Dict[str, Any]]:
        """מחזיר טלפון בודד לפי ID"""
        for phone in self.phones:
            if phone.id == phone_id:
                return asdict(phone)
        return None
    
    async def get_users(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """מחזיר את כל המשתמשים, או מסנן לפי מחלקה"""
        users = self.users
        if department:
            users = [u for u in users if u.department == department]
        return [asdict(user) for user in users]
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """מחזיר משתמש בודד לפי ID"""
        for user in self.users:
            if user.user_id == user_id:
                return asdict(user)
        return None
    
    async def get_lines(self, partition: Optional[str] = None) -> List[Dict[str, Any]]:
        """מחזיר את כל הקווים, או מסנן לפי partition"""
        lines = self.lines
        if partition:
            lines = [l for l in lines if l.partition == partition]
        return [asdict(line) for line in lines]
    
    async def get_line_by_pattern(self, pattern: str) -> Optional[Dict[str, Any]]:
        """מחזיר קו בודד לפי pattern"""
        for line in self.lines:
            if line.pattern == pattern:
                return asdict(line)
        return None
    
    async def create_phone(self, phone_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """יוצר טלפון חדש"""
        new_phone = CUCMPhone(
            id=f"SEP{phone_data.get('mac_address', '00:00:00:00:00:00').replace(':', '')}",
            name=f"SEP{phone_data.get('mac_address', '00:00:00:00:00:00').replace(':', '')}",
            description=phone_data.get("description", "New Phone"),
            model=phone_data.get("model", "Cisco 7841"),
            mac_address=phone_data.get("mac_address", "00:00:00:00:00:00"),
            ip_address=phone_data.get("ip_address", "10.1.1.200"),
            status="unregistered",
            device_pool=phone_data.get("device_pool", "Default"),
            calling_search_space=phone_data.get("calling_search_space", "CSS-Internal"),
            line_dn=phone_data.get("line_dn", ""),
            line_partition=phone_data.get("line_partition", "PT-Internal"),
            last_registered=datetime.utcnow().isoformat() + "Z"
        )
        self.phones.append(new_phone)
        return asdict(new_phone)
    
    async def delete_phone(self, phone_id: str) -> Dict[str, Any]:
        """מוחק טלפון"""
        for i, phone in enumerate(self.phones):
            if phone.id == phone_id:
                self.phones.pop(i)
                return {"deleted": True, "phone_id": phone_id}
        return {"deleted": False, "reason": "not_found"}
    
    def get_stats(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות"""
        return {
            "total_phones": len(self.phones),
            "registered_phones": len([p for p in self.phones if p.status == "registered"]),
            "total_users": len(self.users),
            "active_users": len([u for u in self.users if u.status == "active"]),
            "total_lines": len(self.lines),
            "active_lines": len([l for l in self.lines if l.status == "active"])
        }

# מופע סינגלטון גלובלי
cucm_mock_service = CUCMMockService()
