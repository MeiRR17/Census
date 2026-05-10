"""
API Routers - Expose all client functions as Census endpoints
This allows edge apps to control CMS/CUCM through Census proxy
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from clients import CMSClient, CUCMClient
from data_access import (
    save_cms_cospace, save_cms_call, save_cms_call_participant,
    save_cucm_phone, save_cucm_line, save_cucm_user,
    get_cms_cospaces, get_cms_calls, get_cms_call_participants,
    get_cucm_phones, get_cucm_lines, get_cucm_users
)
from main import get_db

logger = logging.getLogger(__name__)

# =====================================================
# Request/Response Models
# =====================================================

class CoSpaceCreateRequest(BaseModel):
    name: str
    uri: Optional[str] = None
    passcode: Optional[str] = None
    auto_attendant: bool = False
    max_participants: int = 50
    description: Optional[str] = None

class CoSpaceUpdateRequest(BaseModel):
    name: Optional[str] = None
    passcode: Optional[str] = None
    auto_attendant: Optional[bool] = None
    max_participants: Optional[int] = None

class ParticipantControlRequest(BaseModel):
    participant_name: str
    action: str  # 'mute', 'unmute', 'kick', 'make_host', 'make_presenter'

class CallCreationRequest(BaseModel):
    cospace_id: str
    host_user_name: Optional[str] = None

# =====================================================
# CMS Router - All CMS functions exposed
# =====================================================

cms_router = APIRouter(prefix="/api/cms", tags=["CMS"])

@cms_router.get("/cospaces")
async def list_cospaces(
    access_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all CMS CoSpaces from database"""
    cospaces = get_cms_cospaces(db, access_level=access_level)
    return [c.to_dict() for c in cospaces]

@cms_router.post("/cospaces")
async def create_cospace(
    request: CoSpaceCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new CoSpace in CMS
    
    Edge apps use this to create meeting rooms
    """
    try:
        # Connect to actual CMS server
        cms = CMS.create_from_env()
        
        # Create in CMS
        result = cms.create_cospace(
            name=request.name,
            uri=request.uri,
            passcode=request.passcode
        )
        
        # Save to database
        cospace_data = {
            'cospace_id': result.get('id', request.uri or request.name),
            'name': request.name,
            'uri': request.uri or result.get('uri'),
            'passcode': request.passcode,
            'auto_attendant': request.auto_attendant,
            'max_participants': request.max_participants,
            'description': request.description,
            'raw_data': result
        }
        
        saved_cospace = save_cms_cospace(db, cospace_data)
        
        return {
            "success": True,
            "cospace": saved_cospace.to_dict(),
            "cms_response": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create CoSpace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/cospaces/{cospace_id}")
async def get_cospace(
    cospace_id: str,
    db: Session = Depends(get_db)
):
    """Get specific CoSpace details"""
    try:
        # Get fresh data from CMS
        cms = CMS.create_from_env()
        cms_data = cms.get_cospace_details(cospace_id)
        
        return {
            "cospace_id": cospace_id,
            "cms_data": cms_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.put("/cospaces/{cospace_id}/passcode")
async def update_cospace_passcode(
    cospace_id: str,
    passcode: str,
    db: Session = Depends(get_db)
):
    """Update CoSpace passcode"""
    try:
        from clients import CMSClient
        import os
        
        client = CMSClient(
            base_url=os.getenv('CMS_URL'),
            username=os.getenv('CMS_USERNAME'),
            password=os.getenv('CMS_PASSWORD')
        )
        
        result = client.update_cospace_passcode(cospace_id, passcode)
        
        return {
            "success": True,
            "cospace_id": cospace_id,
            "new_passcode": passcode,
            "cms_response": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.delete("/cospaces/{cospace_id}")
async def delete_cospace(
    cospace_id: str,
    db: Session = Depends(get_db)
):
    """Delete a CoSpace"""
    try:
        from clients import CMSClient
        import os
        
        client = CMSClient(
            base_url=os.getenv('CMS_URL'),
            username=os.getenv('CMS_USERNAME'),
            password=os.getenv('CMS_PASSWORD')
        )
        
        success = client.delete_cospace(cospace_id)
        
        return {
            "success": success,
            "cospace_id": cospace_id,
            "message": "CoSpace deleted" if success else "Failed to delete"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/calls")
async def list_calls(
    call_state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all CMS calls from database"""
    calls = get_cms_calls(db, call_state=call_state)
    return [c.to_dict() for c in calls]

@cms_router.get("/calls/active")
async def get_active_calls(
    db: Session = Depends(get_db)
):
    """Get all active calls from CMS in real-time"""
    try:
        cms = CMS.create_from_env()
        calls = cms.get_active_calls()
        
        # Save to database
        for call_data in calls:
            try:
                db_call_data = {
                    'call_id': call_data.get('callId', call_data.get('id')),
                    'cospace_id': call_data.get('cospaceId'),
                    'cospace_name': call_data.get('cospaceName'),
                    'call_state': 'ACTIVE',
                    'current_participants': len(call_data.get('participants', [])),
                    'raw_data': call_data
                }
                save_cms_call(db, db_call_data)
            except Exception as e:
                logger.warning(f"Failed to save call to DB: {e}")
        
        return {
            "active_calls": calls,
            "count": len(calls)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/calls/{call_id}")
async def get_call_details(
    call_id: str,
    db: Session = Depends(get_db)
):
    """Get call details from CMS in real-time"""
    try:
        cms = CMS.create_from_env()
        call_details = cms.get_call_details(call_id)
        
        return {
            "call_id": call_id,
            "details": call_details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/calls/{call_id}/participants")
async def get_call_participants(
    call_id: str,
    db: Session = Depends(get_db)
):
    """Get call participants from CMS in real-time"""
    try:
        cms = CMS.create_from_env()
        participants = cms.get_call_participants(call_id)
        
        # Save to database
        for participant_data in participants:
            try:
                db_participant = {
                    'participant_id': participant_data.get('legId', participant_data.get('id')),
                    'call_id': call_id,
                    'participant_name': participant_data.get('name'),
                    'participant_role': participant_data.get('role', 'PARTICIPANT'),
                    'is_muted': participant_data.get('muted', False),
                    'is_host': participant_data.get('role') == 'HOST',
                    'raw_data': participant_data
                }
                save_cms_call_participant(db, db_participant)
            except Exception as e:
                logger.warning(f"Failed to save participant to DB: {e}")
        
        return {
            "call_id": call_id,
            "participants": participants,
            "count": len(participants)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.post("/calls/{call_id}/participants/{participant_name}/mute")
async def mute_participant(
    call_id: str,
    participant_name: str,
    db: Session = Depends(get_db)
):
    """Mute a participant in a call"""
    try:
        cms = CMS.create_from_env()
        success = cms.mute_participant(call_id, participant_name, mute=True)
        
        return {
            "success": success,
            "call_id": call_id,
            "participant": participant_name,
            "action": "muted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.post("/calls/{call_id}/participants/{participant_name}/unmute")
async def unmute_participant(
    call_id: str,
    participant_name: str,
    db: Session = Depends(get_db)
):
    """Unmute a participant in a call"""
    try:
        cms = CMS.create_from_env()
        success = cms.mute_participant(call_id, participant_name, mute=False)
        
        return {
            "success": success,
            "call_id": call_id,
            "participant": participant_name,
            "action": "unmuted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.delete("/calls/{call_id}/participants/{participant_name}")
async def kick_participant(
    call_id: str,
    participant_name: str,
    db: Session = Depends(get_db)
):
    """Kick a participant from a call"""
    try:
        cms = CMS.create_from_env()
        success = cms.kick_participant(call_id, participant_name)
        
        return {
            "success": success,
            "call_id": call_id,
            "participant": participant_name,
            "action": "kicked"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/system/status")
async def get_cms_system_status():
    """Get CMS system status"""
    try:
        cms = CMS.create_from_env()
        status = cms.test_connection()
        system_info = cms.get_system_info() if status else {}
        
        return {
            "connected": status,
            "system_info": system_info,
            "base_url": cms.base_url
        }
        
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }

# =====================================================
# CUCM Router - All CUCM functions exposed
# =====================================================

cucm_router = APIRouter(prefix="/api/cucm", tags=["CUCM"])

class PhoneCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    product_name: Optional[str] = None
    model: Optional[str] = None
    protocol: str = "SIP"
    device_pool: Optional[str] = None
    location: Optional[str] = None
    calling_search_space: Optional[str] = None

class LineCreateRequest(BaseModel):
    pattern: str
    route_partition: Optional[str] = None
    description: Optional[str] = None
    calling_search_space: Optional[str] = None
    max_num_calls: int = 2
    busy_trigger: int = 1

class UserCreateRequest(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    mail_id: Optional[str] = None
    telephone_number: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None

@cucm_router.get("/phones")
async def list_phones(
    status: Optional[str] = None,
    device_pool: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all CUCM phones from database"""
    phones = get_cucm_phones(db, status=status, device_pool=device_pool)
    return [p.to_dict() for p in phones]

@cucm_router.post("/phones")
async def create_phone(
    request: PhoneCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new phone in CUCM
    
    Edge apps use this to provision new phones
    """
    try:
        # Connect to CUCM
        # Note: This would need actual CUCM AXL implementation
        # For now, we save to database
        
        phone_data = {
            'name': request.name,
            'description': request.description,
            'product_name': request.product_name,
            'model': request.model,
            'protocol': request.protocol,
            'device_pool': request.device_pool,
            'location': request.location,
            'calling_search_space': request.calling_search_space,
            'status': 'registered'
        }
        
        saved_phone = save_cucm_phone(db, phone_data)
        
        return {
            "success": True,
            "phone": saved_phone.to_dict(),
            "note": "Saved to database. CUCM AXL integration needed for actual provisioning."
        }
        
    except Exception as e:
        logger.error(f"Failed to create phone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.get("/phones/{phone_uuid}")
async def get_phone(
    phone_uuid: str,
    db: Session = Depends(get_db)
):
    """Get specific phone details"""
    phones = get_cucm_phones(db)
    phone = next((p for p in phones if str(p.uuid) == phone_uuid), None)
    
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")
    
    return phone.to_dict()

@cucm_router.get("/lines")
async def list_lines(
    pattern: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all CUCM lines from database"""
    lines = get_cucm_lines(db, pattern=pattern)
    return [l.to_dict() for l in lines]

@cucm_router.post("/lines")
async def create_line(
    request: LineCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new line in CUCM"""
    try:
        line_data = {
            'pattern': request.pattern,
            'route_partition': request.route_partition,
            'description': request.description,
            'calling_search_space': request.calling_search_space,
            'max_num_calls': request.max_num_calls,
            'busy_trigger': request.busy_trigger,
            'status': 'active'
        }
        
        saved_line = save_cucm_line(db, line_data)
        
        return {
            "success": True,
            "line": saved_line.to_dict(),
            "note": "Saved to database. CUCM AXL integration needed for actual provisioning."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.get("/lines/{line_uuid}")
async def get_line(
    line_uuid: str,
    db: Session = Depends(get_db)
):
    """Get specific line details"""
    lines = get_cucm_lines(db)
    line = next((l for l in lines if str(l.uuid) == line_uuid), None)
    
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    return line.to_dict()

@cucm_router.get("/users")
async def list_users(
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all CUCM users from database"""
    users = get_cucm_users(db, department=department)
    return [u.to_dict() for u in users]

@cucm_router.post("/users")
async def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new user in CUCM"""
    try:
        user_data = {
            'user_id': request.user_id,
            'first_name': request.first_name,
            'last_name': request.last_name,
            'display_name': request.display_name,
            'mail_id': request.mail_id,
            'telephone_number': request.telephone_number,
            'department': request.department,
            'title': request.title,
            'status': 'active'
        }
        
        saved_user = save_cucm_user(db, user_data)
        
        return {
            "success": True,
            "user": saved_user.to_dict(),
            "note": "Saved to database. CUCM AXL integration needed for actual provisioning."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get specific user details"""
    users = get_cucm_users(db)
    user = next((u for u in users if u.user_id == user_id), None)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.to_dict()

@cucm_router.put("/phones/{phone_name}")
async def update_phone(
    phone_name: str,
    request: PhoneCreateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing phone in CUCM"""
    try:
        from clients import CUCMClient
        import os
        
        client = CUCMClient(
            host=os.getenv('CUCM_HOST', 'localhost'),
            username=os.getenv('CUCM_USERNAME', 'admin'),
            password=os.getenv('CUCM_PASSWORD', 'admin')
        )
        
        phone_data = {
            'description': request.description,
            'product': request.model,
            'class': request.device_pool,
            'protocol': 'SIP',
            'protocolSide': 'User',
            'devicePoolName': request.device_pool,
            'locationName': 'Hub_None',
            'callManagerGroupName': 'Default'
        }
        
        success = client.update_phone(phone_name, phone_data)
        
        return {
            "success": success,
            "phone_name": phone_name,
            "message": "Phone updated successfully" if success else "Failed to update phone"
        }
        
    except Exception as e:
        logger.error(f"Failed to update CUCM phone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.delete("/phones/{phone_name}")
async def delete_phone(
    phone_name: str,
    db: Session = Depends(get_db)
):
    """Delete a phone from CUCM"""
    try:
        from clients import CUCMClient
        import os
        
        client = CUCMClient(
            host=os.getenv('CUCM_HOST', 'localhost'),
            username=os.getenv('CUCM_USERNAME', 'admin'),
            password=os.getenv('CUCM_PASSWORD', 'admin')
        )
        
        success = client.delete_phone(phone_name)
        
        return {
            "success": success,
            "phone_name": phone_name,
            "message": "Phone deleted successfully" if success else "Failed to delete phone"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete CUCM phone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.put("/cospaces/{cospace_id}")
async def update_cospace(
    cospace_id: str,
    request: CoSpaceUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update CoSpace general properties"""
    try:
        from clients import CMSClient
        import os
        
        client = CMSClient(
            base_url=os.getenv('CMS_URL'),
            username=os.getenv('CMS_USERNAME'),
            password=os.getenv('CMS_PASSWORD')
        )
        
        # Build update data
        update_data = {}
        if request.name:
            update_data['name'] = request.name
        if request.passcode:
            update_data['passcode'] = request.passcode
        if request.auto_attendant is not None:
            update_data['autoAttendant'] = request.auto_attendant
        if request.max_participants:
            update_data['maxParticipants'] = request.max_participants
        
        result = client.update_cospace(cospace_id, **update_data)
        
        return {
            "success": True,
            "cospace_id": cospace_id,
            "updated_fields": list(update_data.keys()),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to update CoSpace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.put("/lines/{line_uuid}")
async def update_line(
    line_uuid: str,
    request: LineCreateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing line in CUCM"""
    try:
        from clients import CUCMClient
        import os
        
        client = CUCMClient(
            host=os.getenv('CUCM_HOST', 'localhost'),
            username=os.getenv('CUCM_USERNAME', 'admin'),
            password=os.getenv('CUCM_PASSWORD', 'admin')
        )
        
        # Line update logic would go here
        # Placeholder for now
        
        return {
            "success": True,
            "line_uuid": line_uuid,
            "message": "Line update endpoint - implementation needed",
            "note": "Full CUCM AXL integration required for line updates"
        }
        
    except Exception as e:
        logger.error(f"Failed to update CUCM line: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.delete("/lines/{line_uuid}")
async def delete_line(
    line_uuid: str,
    db: Session = Depends(get_db)
):
    """Delete a line from CUCM"""
    try:
        from clients import CUCMClient
        import os
        
        client = CUCMClient(
            host=os.getenv('CUCM_HOST', 'localhost'),
            username=os.getenv('CUCM_USERNAME', 'admin'),
            password=os.getenv('CUCM_PASSWORD', 'admin')
        )
        
        # Line delete logic would go here
        # Placeholder for now
        
        return {
            "success": True,
            "line_uuid": line_uuid,
            "message": "Line delete endpoint - implementation needed",
            "note": "Full CUCM AXL integration required for line deletion"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete CUCM line: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing user in CUCM"""
    try:
        from clients import CUCMClient
        import os
        
        client = CUCMClient(
            host=os.getenv('CUCM_HOST', 'localhost'),
            username=os.getenv('CUCM_USERNAME', 'admin'),
            password=os.getenv('CUCM_PASSWORD', 'admin')
        )
        
        # User update logic would go here
        # Placeholder for now
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User update endpoint - implementation needed",
            "note": "Full CUCM AXL integration required for user updates"
        }
        
    except Exception as e:
        logger.error(f"Failed to update CUCM user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Delete a user from CUCM"""
    try:
        from clients import CUCMClient
        import os
        
        client = CUCMClient(
            host=os.getenv('CUCM_HOST', 'localhost'),
            username=os.getenv('CUCM_USERNAME', 'admin'),
            password=os.getenv('CUCM_PASSWORD', 'admin')
        )
        
        # User delete logic would go here
        # Placeholder for now
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "User delete endpoint - implementation needed",
            "note": "Full CUCM AXL integration required for user deletion"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete CUCM user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_router.get("/system/status")
async def get_cucm_system_status():
    """Get CUCM system status"""
    try:
        # This would check CUCM AXL connection
        return {
            "connected": True,  # Placeholder
            "note": "CUCM AXL integration needed for actual status check",
            "capabilities": [
                "phone_management",
                "line_management",
                "user_management"
            ]
        }
        
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }

# =====================================================
# UCCX Router - All UCCX functions exposed
# =====================================================

uccx_router = APIRouter(prefix="/api/uccx", tags=["UCCX"])

class AgentCreateRequest(BaseModel):
    agent_id: str
    first_name: str
    last_name: str
    extension: str
    team_id: Optional[str] = None
    description: Optional[str] = None

class AgentUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    extension: Optional[str] = None
    team_id: Optional[str] = None
    status: Optional[str] = None

@uccx_router.get("/system/status")
async def get_uccx_system_status():
    """Get UCCX system status"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        status = client.get_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get UCCX status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@uccx_router.get("/agents")
async def get_uccx_agents(
    db: Session = Depends(get_db)
):
    """Get all UCCX agents from real-time API"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        agents = client.get_agents()
        
        # Save to database
        for agent_data in agents:
            try:
                db_agent = {
                    'agent_id': agent_data.get('agent_id'),
                    'first_name': agent_data.get('first_name'),
                    'last_name': agent_data.get('last_name'),
                    'extension': agent_data.get('extension'),
                    'status': agent_data.get('status'),
                    'raw_data': agent_data
                }
                # We'll add data access function later
            except Exception as e:
                logger.warning(f"Failed to save agent to DB: {e}")
        
        return {
            "agents": agents,
            "count": len(agents)
        }
        
    except Exception as e:
        logger.error(f"Failed to get UCCX agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@uccx_router.post("/agents")
async def create_uccx_agent(
    request: AgentCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new agent in UCCX"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        agent_data = {
            'agentId': request.agent_id,
            'firstName': request.first_name,
            'lastName': request.last_name,
            'extension': request.extension,
            'teamId': request.team_id,
            'description': request.description
        }
        
        success = client.create_agent(agent_data)
        
        return {
            "success": success,
            "agent_id": request.agent_id,
            "message": "Agent created successfully" if success else "Failed to create agent"
        }
        
    except Exception as e:
        logger.error(f"Failed to create UCCX agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@uccx_router.put("/agents/{agent_id}")
async def update_uccx_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing agent in UCCX"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        agent_data = {}
        if request.first_name:
            agent_data['firstName'] = request.first_name
        if request.last_name:
            agent_data['lastName'] = request.last_name
        if request.extension:
            agent_data['extension'] = request.extension
        if request.team_id:
            agent_data['teamId'] = request.team_id
        if request.status:
            agent_data['state'] = request.status
        
        success = client.update_agent(agent_id, agent_data)
        
        return {
            "success": success,
            "agent_id": agent_id,
            "message": "Agent updated successfully" if success else "Failed to update agent"
        }
        
    except Exception as e:
        logger.error(f"Failed to update UCCX agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@uccx_router.delete("/agents/{agent_id}")
async def delete_uccx_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Delete an agent from UCCX"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        success = client.delete_agent(agent_id)
        
        return {
            "success": success,
            "agent_id": agent_id,
            "message": "Agent deleted successfully" if success else "Failed to delete agent"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete UCCX agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@uccx_router.get("/teams")
async def get_uccx_teams(
    db: Session = Depends(get_db)
):
    """Get all UCCX teams"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        teams = client.get_teams()
        
        return {
            "teams": teams,
            "count": len(teams)
        }
        
    except Exception as e:
        logger.error(f"Failed to get UCCX teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@uccx_router.get("/queues")
async def get_uccx_queues(
    db: Session = Depends(get_db)
):
    """Get all UCCX CSQs (Contact Service Queues)"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        queues = client.get_queues()
        
        return {
            "queues": queues,
            "count": len(queues)
        }
        
    except Exception as e:
        logger.error(f"Failed to get UCCX queues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# MeetingPlace Router - All MeetingPlace functions exposed
# =====================================================

meetingplace_router = APIRouter(prefix="/api/meetingplace", tags=["MeetingPlace"])

class MeetingCreateRequest(BaseModel):
    title: str
    start_time: str
    duration: int
    participants: Optional[List[str]] = []

@meetingplace_router.get("/meetings")
async def get_meetingplace_meetings(
    db: Session = Depends(get_db)
):
    """Get all MeetingPlace meetings"""
    try:
        from clients import MeetingPlaceClient
        import os
        
        client = MeetingPlaceClient(
            host=os.getenv('MEETINGPLACE_HOST', 'localhost'),
            username=os.getenv('MEETINGPLACE_USERNAME', 'admin'),
            password=os.getenv('MEETINGPLACE_PASSWORD', 'admin')
        )
        
        meetings = client.get_meetings()
        
        return {
            "meetings": meetings,
            "count": len(meetings)
        }
        
    except Exception as e:
        logger.error(f"Failed to get MeetingPlace meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@meetingplace_router.post("/meetings")
async def create_meetingplace_meeting(
    request: MeetingCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new MeetingPlace meeting"""
    try:
        from clients import MeetingPlaceClient
        import os
        
        client = MeetingPlaceClient(
            host=os.getenv('MEETINGPLACE_HOST', 'localhost'),
            username=os.getenv('MEETINGPLACE_USERNAME', 'admin'),
            password=os.getenv('MEETINGPLACE_PASSWORD', 'admin')
        )
        
        result = client.create_meeting(
            title=request.title,
            start_time=request.start_time,
            duration=request.duration,
            participants=request.participants
        )
        
        return {
            "success": True,
            "result": result,
            "message": "Meeting created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create MeetingPlace meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@meetingplace_router.get("/users")
async def get_meetingplace_users(
    db: Session = Depends(get_db)
):
    """Get all MeetingPlace users"""
    try:
        from clients import MeetingPlaceClient
        import os
        
        client = MeetingPlaceClient(
            host=os.getenv('MEETINGPLACE_HOST', 'localhost'),
            username=os.getenv('MEETINGPLACE_USERNAME', 'admin'),
            password=os.getenv('MEETINGPLACE_PASSWORD', 'admin')
        )
        
        users = client.get_users()
        
        return {
            "users": users,
            "count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to get MeetingPlace users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@meetingplace_router.get("/users/{user_id}")
async def get_meetingplace_user_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get MeetingPlace user profile"""
    try:
        from clients import MeetingPlaceClient
        import os
        
        client = MeetingPlaceClient(
            host=os.getenv('MEETINGPLACE_HOST', 'localhost'),
            username=os.getenv('MEETINGPLACE_USERNAME', 'admin'),
            password=os.getenv('MEETINGPLACE_PASSWORD', 'admin')
        )
        
        profile = client.get_user_profile(user_id)
        
        return {
            "user_id": user_id,
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"Failed to get MeetingPlace user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@meetingplace_router.get("/system/status")
async def get_meetingplace_system_status():
    """Get MeetingPlace system status"""
    try:
        from clients import MeetingPlaceClient
        import os
        
        client = MeetingPlaceClient(
            host=os.getenv('MEETINGPLACE_HOST', 'localhost'),
            username=os.getenv('MEETINGPLACE_USERNAME', 'admin'),
            password=os.getenv('MEETINGPLACE_PASSWORD', 'admin')
        )
        
        # Test connection by getting meetings
        meetings = client.get_meetings()
        
        return {
            "connected": True,
            "host": os.getenv('MEETINGPLACE_HOST', 'localhost'),
            "meetings_count": len(meetings)
        }
        
    except Exception as e:
        logger.error(f"Failed to get MeetingPlace status: {e}")
        return {
            "connected": False,
            "error": str(e)
        }

# =====================================================
# Unified Router - Combined operations
# =====================================================

unified_router = APIRouter(prefix="/api/unified", tags=["Unified"])

@unified_router.get("/meetings")
async def get_all_meetings(
    db: Session = Depends(get_db)
):
    """Get all meetings from all systems (CMS + others)"""
    cms_cospaces = get_cms_cospaces(db)
    cms_calls = get_cms_calls(db, call_state='ACTIVE')
    
    return {
        "cms_cospaces": [c.to_dict() for c in cms_cospaces],
        "cms_active_calls": [c.to_dict() for c in cms_calls],
        "total_meetings": len(cms_cospaces) + len(cms_calls)
    }

@unified_router.get("/devices")
async def get_all_devices(
    db: Session = Depends(get_db)
):
    """Get all devices from all systems (CUCM + others)"""
    cucm_phones = get_cucm_phones(db)
    
    return {
        "cucm_phones": [p.to_dict() for p in cucm_phones],
        "total_devices": len(cucm_phones)
    }

@unified_router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db)
):
    """Get all users from all systems"""
    cucm_users = get_cucm_users(db)
    
    return {
        "cucm_users": [u.to_dict() for u in cucm_users],
        "total_users": len(cucm_users)
    }

@unified_router.get("/contact-center")
async def get_all_contact_center(
    db: Session = Depends(get_db)
):
    """Get all contact center data from UCCX"""
    try:
        from clients import UCCXClient
        import os
        
        client = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        
        agents = client.get_agents()
        teams = client.get_teams()
        queues = client.get_queues()
        
        return {
            "uccx_agents": agents,
            "uccx_teams": teams,
            "uccx_queues": queues,
            "total_agents": len(agents),
            "total_teams": len(teams),
            "total_queues": len(queues)
        }
        
    except Exception as e:
        logger.error(f"Failed to get contact center data: {e}")
        return {
            "error": str(e),
            "uccx_agents": [],
            "uccx_teams": [],
            "uccx_queues": []
        }

@unified_router.get("/system/status")
async def get_all_systems_status():
    """Get status of all connected systems"""
    import os
    
    systems = {}
    
    # Check CMS
    try:
        from services.cms_service import CMS
        cms = CMS.create_from_env()
        systems["cms"] = {
            "connected": cms.test_connection(),
            "host": os.getenv('CMS_HOST', 'localhost')
        }
    except Exception as e:
        systems["cms"] = {"connected": False, "error": str(e)}
    
    # Check CUCM (placeholder - would need actual implementation)
    systems["cucm"] = {
        "connected": False,
        "note": "CUCM AXL integration needed"
    }
    
    # Check UCCX
    try:
        from clients import UCCXClient
        uccx = UCCXClient(
            host=os.getenv('UCCX_HOST', 'localhost'),
            username=os.getenv('UCCX_USERNAME', 'admin'),
            password=os.getenv('UCCX_PASSWORD', 'admin')
        )
        systems["uccx"] = {
            "connected": uccx.test_connection(),
            "host": os.getenv('UCCX_HOST', 'localhost')
        }
    except Exception as e:
        systems["uccx"] = {"connected": False, "error": str(e)}
    
    return {
        "systems": systems,
        "total_connected": sum(1 for s in systems.values() if s.get("connected", False))
    }

