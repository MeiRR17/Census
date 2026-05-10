"""
Data Access Layer - Functions to save data from clients to database
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import (
    CUCMPhone, CUCMLine, CUCMUser,
    CMSCoSpace, CMSCall, CMSCallParticipant
)
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# =====================================================
# CUCM Data Access Functions
# =====================================================

def save_cucm_phone(db: Session, phone_data: Dict[str, Any]) -> CUCMPhone:
    """Save or update CUCM phone in database"""
    try:
        # Check if phone already exists
        existing = db.query(CUCMPhone).filter(
            CUCMPhone.name == phone_data.get('name')
        ).first()
        
        if existing:
            # Update existing phone
            for key, value in phone_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated CUCM phone: {existing.name}")
            return existing
        else:
            # Create new phone
            phone = CUCMPhone(
                name=phone_data.get('name'),
                description=phone_data.get('description'),
                product_name=phone_data.get('product_name'),
                model=phone_data.get('model'),
                protocol=phone_data.get('protocol', 'SIP'),
                ip_address=phone_data.get('ip_address'),
                mac_address=phone_data.get('mac_address'),
                device_pool=phone_data.get('device_pool'),
                calling_search_space=phone_data.get('calling_search_space'),
                device_security_profile=phone_data.get('device_security_profile'),
                sip_profile=phone_data.get('sip_profile'),
                location=phone_data.get('location'),
                status=phone_data.get('status', 'registered'),
                raw_data=phone_data.get('raw_data', {})
            )
            db.add(phone)
            db.commit()
            db.refresh(phone)
            logger.info(f"Created CUCM phone: {phone.name}")
            return phone
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save CUCM phone: {e}")
        raise

def save_cucm_line(db: Session, line_data: Dict[str, Any]) -> CUCMLine:
    """Save or update CUCM line in database"""
    try:
        existing = db.query(CUCMLine).filter(
            CUCMLine.pattern == line_data.get('pattern'),
            CUCMLine.route_partition == line_data.get('route_partition')
        ).first()
        
        if existing:
            for key, value in line_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated CUCM line: {existing.pattern}")
            return existing
        else:
            line = CUCMLine(
                pattern=line_data.get('pattern'),
                description=line_data.get('description'),
                route_partition=line_data.get('route_partition'),
                calling_search_space=line_data.get('calling_search_space'),
                max_num_calls=line_data.get('max_num_calls', 2),
                busy_trigger=line_data.get('busy_trigger', 1),
                status=line_data.get('status', 'active'),
                raw_data=line_data.get('raw_data', {})
            )
            db.add(line)
            db.commit()
            db.refresh(line)
            logger.info(f"Created CUCM line: {line.pattern}")
            return line
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save CUCM line: {e}")
        raise

def save_cucm_user(db: Session, user_data: Dict[str, Any]) -> CUCMUser:
    """Save or update CUCM user in database"""
    try:
        existing = db.query(CUCMUser).filter(
            CUCMUser.user_id == user_data.get('user_id')
        ).first()
        
        if existing:
            for key, value in user_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated CUCM user: {existing.user_id}")
            return existing
        else:
            user = CUCMUser(
                user_id=user_data.get('user_id'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                display_name=user_data.get('display_name'),
                mail_id=user_data.get('mail_id'),
                telephone_number=user_data.get('telephone_number'),
                mobile_number=user_data.get('mobile_number'),
                department=user_data.get('department'),
                manager=user_data.get('manager'),
                title=user_data.get('title'),
                associated_devices=user_data.get('associated_devices', []),
                associated_lines=user_data.get('associated_lines', []),
                user_groups=user_data.get('user_groups', []),
                status=user_data.get('status', 'active'),
                raw_data=user_data.get('raw_data', {})
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created CUCM user: {user.user_id}")
            return user
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save CUCM user: {e}")
        raise

def get_cucm_phones(db: Session, **filters) -> List[CUCMPhone]:
    """Query CUCM phones with filters"""
    query = db.query(CUCMPhone)
    
    if filters.get('status'):
        query = query.filter(CUCMPhone.status == filters['status'])
    if filters.get('device_pool'):
        query = query.filter(CUCMPhone.device_pool == filters['device_pool'])
    if filters.get('model'):
        query = query.filter(CUCMPhone.model == filters['model'])
    
    return query.all()

def get_cucm_lines(db: Session, **filters) -> List[CUCMLine]:
    """Query CUCM lines with filters"""
    query = db.query(CUCMLine)
    
    if filters.get('pattern'):
        query = query.filter(CUCMLine.pattern.like(f"%{filters['pattern']}%"))
    if filters.get('route_partition'):
        query = query.filter(CUCMLine.route_partition == filters['route_partition'])
    
    return query.all()

def get_cucm_users(db: Session, **filters) -> List[CUCMUser]:
    """Query CUCM users with filters"""
    query = db.query(CUCMUser)
    
    if filters.get('department'):
        query = query.filter(CUCMUser.department == filters['department'])
    if filters.get('status'):
        query = query.filter(CUCMUser.status == filters['status'])
    
    return query.all()

# =====================================================
# CMS Data Access Functions
# =====================================================

def save_cms_cospace(db: Session, cospace_data: Dict[str, Any]) -> CMSCoSpace:
    """Save or update CMS CoSpace in database"""
    try:
        existing = db.query(CMSCoSpace).filter(
            CMSCoSpace.cospace_id == cospace_data.get('cospace_id')
        ).first()
        
        if existing:
            # Update existing cospace
            for key, value in cospace_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated CMS CoSpace: {existing.name}")
            return existing
        else:
            # Create new cospace
            cospace = CMSCoSpace(
                cospace_id=cospace_data.get('cospace_id'),
                name=cospace_data.get('name'),
                uri=cospace_data.get('uri'),
                description=cospace_data.get('description'),
                passcode=cospace_data.get('passcode'),
                auto_attendant=cospace_data.get('auto_attendant', False),
                owner_id=cospace_data.get('owner_id'),
                owner_name=cospace_data.get('owner_name'),
                access_level=cospace_data.get('access_level', 'PUBLIC'),
                cospace_type=cospace_data.get('cospace_type', 'MEETING'),
                max_participants=cospace_data.get('max_participants', 50),
                max_video_resolution=cospace_data.get('max_video_resolution', 'HD'),
                enable_chat=cospace_data.get('enable_chat', True),
                enable_recording=cospace_data.get('enable_recording', False),
                enable_live_streaming=cospace_data.get('enable_live_streaming', False),
                status=cospace_data.get('status', 'active'),
                raw_data=cospace_data.get('raw_data', {})
            )
            db.add(cospace)
            db.commit()
            db.refresh(cospace)
            logger.info(f"Created CMS CoSpace: {cospace.name}")
            return cospace
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save CMS CoSpace: {e}")
        raise

def save_cms_call(db: Session, call_data: Dict[str, Any]) -> CMSCall:
    """Save or update CMS call in database"""
    try:
        existing = db.query(CMSCall).filter(
            CMSCall.call_id == call_data.get('call_id')
        ).first()
        
        if existing:
            # Update existing call
            for key, value in call_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated CMS call: {existing.call_id}")
            return existing
        else:
            # Create new call
            call = CMSCall(
                call_id=call_data.get('call_id'),
                cospace_id=call_data.get('cospace_id'),
                cospace_name=call_data.get('cospace_name'),
                cospace_uri=call_data.get('cospace_uri'),
                call_type=call_data.get('call_type', 'MEETING'),
                call_state=call_data.get('call_state', 'ACTIVE'),
                start_time=call_data.get('start_time'),
                end_time=call_data.get('end_time'),
                duration=call_data.get('duration', 0),
                host_user_id=call_data.get('host_user_id'),
                host_user_name=call_data.get('host_user_name'),
                current_participants=call_data.get('current_participants', 0),
                max_participants=call_data.get('max_participants', 50),
                enable_chat=call_data.get('enable_chat', True),
                enable_recording=call_data.get('enable_recording', False),
                enable_live_streaming=call_data.get('enable_live_streaming', False),
                status=call_data.get('status', 'active'),
                raw_data=call_data.get('raw_data', {})
            )
            db.add(call)
            db.commit()
            db.refresh(call)
            logger.info(f"Created CMS call: {call.call_id}")
            return call
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save CMS call: {e}")
        raise

def save_cms_call_participant(db: Session, participant_data: Dict[str, Any]) -> CMSCallParticipant:
    """Save or update CMS call participant in database"""
    try:
        existing = db.query(CMSCallParticipant).filter(
            CMSCallParticipant.participant_id == participant_data.get('participant_id')
        ).first()
        
        if existing:
            # Update existing participant
            for key, value in participant_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated CMS participant: {existing.participant_name}")
            return existing
        else:
            # Create new participant
            participant = CMSCallParticipant(
                participant_id=participant_data.get('participant_id'),
                call_id=participant_data.get('call_id'),
                cospace_id=participant_data.get('cospace_id'),
                participant_name=participant_data.get('participant_name'),
                participant_email=participant_data.get('participant_email'),
                participant_role=participant_data.get('participant_role', 'PARTICIPANT'),
                participant_status=participant_data.get('participant_status', 'CONNECTED'),
                join_time=participant_data.get('join_time'),
                leave_time=participant_data.get('leave_time'),
                duration=participant_data.get('duration', 0),
                leg_id=participant_data.get('leg_id'),
                is_host=participant_data.get('is_host', False),
                is_moderator=participant_data.get('is_moderator', False),
                is_presenter=participant_data.get('is_presenter', False),
                is_muted=participant_data.get('is_muted', False),
                is_video_muted=participant_data.get('is_video_muted', False),
                is_content_sharing=participant_data.get('is_content_sharing', False),
                status=participant_data.get('status', 'active'),
                raw_data=participant_data.get('raw_data', {})
            )
            db.add(participant)
            db.commit()
            db.refresh(participant)
            logger.info(f"Created CMS participant: {participant.participant_name}")
            return participant
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save CMS participant: {e}")
        raise

def get_cms_cospaces(db: Session, **filters) -> List[CMSCoSpace]:
    """Query CMS CoSpaces with filters"""
    query = db.query(CMSCoSpace)
    
    if filters.get('access_level'):
        query = query.filter(CMSCoSpace.access_level == filters['access_level'])
    if filters.get('status'):
        query = query.filter(CMSCoSpace.status == filters['status'])
    if filters.get('owner_id'):
        query = query.filter(CMSCoSpace.owner_id == filters['owner_id'])
    
    return query.all()

def get_cms_calls(db: Session, **filters) -> List[CMSCall]:
    """Query CMS calls with filters"""
    query = db.query(CMSCall)
    
    if filters.get('call_state'):
        query = query.filter(CMSCall.call_state == filters['call_state'])
    if filters.get('cospace_id'):
        query = query.filter(CMSCall.cospace_id == filters['cospace_id'])
    if filters.get('status'):
        query = query.filter(CMSCall.status == filters['status'])
    
    return query.all()

def get_cms_call_participants(db: Session, call_id: str) -> List[CMSCallParticipant]:
    """Get participants for a specific call"""
    return db.query(CMSCallParticipant).filter(
        CMSCallParticipant.call_id == call_id
    ).all()

# =====================================================
# Sync Functions
# =====================================================

def sync_cucm_phones(db: Session, phones_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sync multiple CUCM phones to database"""
    created = 0
    updated = 0
    failed = 0
    
    for phone_data in phones_data:
        try:
            phone = save_cucm_phone(db, phone_data)
            if phone.created_at == phone.updated_at:
                created += 1
            else:
                updated += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to sync phone {phone_data.get('name')}: {e}")
    
    return {"created": created, "updated": updated, "failed": failed}

def sync_cms_cospaces(db: Session, cospaces_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sync multiple CMS CoSpaces to database"""
    created = 0
    updated = 0
    failed = 0
    
    for cospace_data in cospaces_data:
        try:
            cospace = save_cms_cospace(db, cospace_data)
            if cospace.created_at == cospace.updated_at:
                created += 1
            else:
                updated += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to sync cospace {cospace_data.get('name')}: {e}")
    
    return {"created": created, "updated": updated, "failed": failed}

def sync_cms_calls(db: Session, calls_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sync multiple CMS calls to database"""
    created = 0
    updated = 0
    failed = 0
    
    for call_data in calls_data:
        try:
            call = save_cms_call(db, call_data)
            if call.created_at == call.updated_at:
                created += 1
            else:
                updated += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to sync call {call_data.get('call_id')}: {e}")
    
    return {"created": created, "updated": updated, "failed": failed}

def sync_cms_call_participants(db: Session, participants_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sync multiple CMS call participants to database"""
    created = 0
    updated = 0
    failed = 0
    
    for participant_data in participants_data:
        try:
            participant = save_cms_call_participant(db, participant_data)
            if participant.created_at == participant.updated_at:
                created += 1
            else:
                updated += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to sync participant {participant_data.get('participant_name')}: {e}")
    
    return {"created": created, "updated": updated, "failed": failed}
