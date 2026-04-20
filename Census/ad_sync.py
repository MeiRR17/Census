#!/usr/bin/env python3
"""
Active Directory Sync - User and Group Synchronization
==============================================

Synchronizes users and groups from Active Directory to CENSUS.
Handles incremental sync, group mapping, and user provisioning.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncpg
import ldap3
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ADUser:
    """Active Directory user information."""
    username: str
    email: str
    full_name: str
    department: str
    title: str
    phone_number: Optional[str] = None
    manager: Optional[str] = None
    groups: List[str] = None
    last_logon: Optional[datetime] = None
    account_enabled: bool = True

@dataclass
class SyncMetrics:
    """Metrics for AD sync operations."""
    total_users: int = 0
    processed_users: int = 0
    new_users: int = 0
    updated_users: int = 0
    disabled_users: int = 0
    errors: int = 0
    start_time: datetime = None
    end_time: Optional[datetime] = None

class ADSync:
    """
    Active Directory synchronization engine.
    
    Features:
    - Incremental user sync (last 7 days)
    - Group mapping and role assignment
    - User provisioning and deprovisioning
    - Resilient connection handling
    """
    
    def __init__(self, ad_server: str, bind_user: str, bind_password: str, 
                 base_dn: str, domain: str):
        self.ad_server = ad_server
        self.bind_user = bind_user
        self.bind_password = bind_password
        self.base_dn = base_dn
        self.domain = domain
        self.connection = None
        self.metrics = SyncMetrics()
    
    async def initialize(self):
        """Initialize AD connection."""
        try:
            # Connect to Active Directory
            server = ldap3.Server(self.ad_server, get_info=ldap3.ALL)
            self.connection = ldap3.Connection(
                server,
                user=self.bind_user,
                password=self.bind_password,
                auto_bind=True
            )
            logger.info(f"Connected to AD server: {self.ad_server}")
        except Exception as e:
            logger.error(f"Failed to connect to AD: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def run_user_sync(self) -> SyncMetrics:
        """
        Run incremental user synchronization from AD.
        
        Returns:
            SyncMetrics with operation results
        """
        logger.info("Starting AD user synchronization")
        self.metrics = SyncMetrics(start_time=datetime.utcnow())
        
        try:
            # Get cutoff time (7 days ago)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            # Search for recently modified users
            ad_users = await self._get_active_directory_users(cutoff_time)
            self.metrics.total_users = len(ad_users)
            
            # Sync users to CENSUS database
            await self._sync_users_to_census(ad_users)
            
            # Update sync metadata
            await self._update_sync_metadata("ad_user_sync")
            
        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"AD sync failed: {e}")
            raise
        
        self.metrics.end_time = datetime.utcnow()
        return self.metrics
    
    async def _get_active_directory_users(self, cutoff_time: datetime) -> List[ADUser]:
        """
        Get users from Active Directory modified since cutoff time.
        
        Uses LDAP filters for efficient querying.
        """
        try:
            # Search for users modified in last 7 days
            search_filter = f"(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(whenChanged>={cutoff_time.strftime('%Y%m%d%H%M%S.0Z')}))"
            
            # Define attributes to retrieve
            attributes = [
                'sAMAccountName',  # username
                'mail',           # email
                'displayName',    # full name
                'department',     # department
                'title',         # job title
                'telephoneNumber', # phone
                'manager',        # manager
                'memberOf',       # group membership
                'lastLogon',      # last logon time
                'userAccountControl'  # account status
            ]
            
            # Perform search
            self.connection.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=attributes,
                size_limit=5000
            )
            
            users = []
            for entry in self.connection.entries:
                try:
                    # Extract user attributes
                    attrs = entry['attributes']
                    
                    # Parse group membership
                    groups = []
                    if 'memberOf' in attrs:
                        for group_dn in attrs['memberOf']:
                            # Extract group name from DN
                            group_name = group_dn.split(',')[0].split('=')[1]
                            groups.append(group_name)
                    
                    # Parse last logon time
                    last_logon = None
                    if 'lastLogon' in attrs and attrs['lastLogon']:
                        try:
                            last_logon = datetime.strptime(attrs['lastLogon'][0], '%Y%m%d%H%M%S.0Z')
                        except (ValueError, IndexError):
                            pass
                    
                    # Check if account is disabled
                    account_enabled = True
                    if 'userAccountControl' in attrs:
                        uac_value = attrs['userAccountControl'][0] if isinstance(attrs['userAccountControl'], list) else attrs['userAccountControl']
                        account_enabled = not (uac_value & 2)  # ACCOUNTDISABLE flag
                    
                    user = ADUser(
                        username=attrs.get('sAMAccountName', [''])[0],
                        email=attrs.get('mail', [''])[0],
                        full_name=attrs.get('displayName', [''])[0],
                        department=attrs.get('department', [''])[0],
                        title=attrs.get('title', [''])[0],
                        phone_number=attrs.get('telephoneNumber', [''])[0] if 'telephoneNumber' in attrs else None,
                        manager=attrs.get('manager', [''])[0] if 'manager' in attrs else None,
                        groups=groups,
                        last_logon=last_logon,
                        account_enabled=account_enabled
                    )
                    
                    users.append(user)
                    
                except Exception as e:
                    logger.error(f"Failed to parse user entry: {e}")
                    continue
            
            logger.info(f"Retrieved {len(users)} users from AD")
            return users
            
        except Exception as e:
            logger.error(f"Failed to query AD: {e}")
            raise
    
    async def _sync_users_to_census(self, ad_users: List[ADUser]):
        """
        Synchronize AD users to CENSUS database.
        
        Handles user creation, updates, and deprovisioning.
        """
        try:
            # In production, this would connect to CENSUS database
            # For demo, we'll simulate the sync process
            
            for user in ad_users:
                try:
                    # Simulate database operations
                    await self._upsert_user_to_census(user)
                    self.metrics.processed_users += 1
                    
                    # Track new vs updated users
                    if self._is_new_user(user):
                        self.metrics.new_users += 1
                        logger.info(f"New user: {user.username}")
                    else:
                        self.metrics.updated_users += 1
                        logger.debug(f"Updated user: {user.username}")
                    
                    # Handle disabled users
                    if not user.account_enabled:
                        await self._disable_user_in_census(user)
                        self.metrics.disabled_users += 1
                        logger.info(f"Disabled user: {user.username}")
                    
                except Exception as e:
                    logger.error(f"Failed to sync user {user.username}: {e}")
                    self.metrics.errors += 1
            
        except Exception as e:
            logger.error(f"Failed to sync users to CENSUS: {e}")
            raise
    
    async def _upsert_user_to_census(self, user: ADUser):
        """
        Upsert user to CENSUS database.
        
        In production, this would use asyncpg to insert/update.
        """
        try:
            # Simulate database upsert
            # In production:
            # await conn.execute("""
            #     INSERT INTO users (
            #         userid, full_name, email, department, title,
            #         phone_number, manager, groups, account_enabled,
            #         last_logon, created_at, updated_at
            #     ) VALUES (
            #         $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            #     )
            #     ON CONFLICT (userid) DO UPDATE SET
            #         full_name = EXCLUDED.full_name,
            #         email = EXCLUDED.email,
            #         department = EXCLUDED.department,
            #         title = EXCLUDED.title,
            #         phone_number = EXCLUDED.phone_number,
            #         manager = EXCLUDED.manager,
            #         groups = EXCLUDED.groups,
            #         account_enabled = EXCLUDED.account_enabled,
            #         last_logon = EXCLUDED.last_logon,
            #         updated_at = CURRENT_TIMESTAMP
            # """, user.username, user.full_name, user.email, user.department,
            # user.title, user.phone_number, user.manager, user.groups,
            # user.account_enabled, user.last_logon)
            
            logger.debug(f"Upserted user {user.username} to CENSUS")
            
        except Exception as e:
            logger.error(f"Failed to upsert user {user.username}: {e}")
            raise
    
    async def _disable_user_in_census(self, user: ADUser):
        """
        Disable user in CENSUS database.
        
        Soft delete - marks as inactive rather than hard delete.
        """
        try:
            # Simulate disabling user
            # In production:
            # await conn.execute("""
            #     UPDATE users 
            #     SET account_enabled = false, updated_at = CURRENT_TIMESTAMP
            #     WHERE userid = $1
            # """, user.username)
            
            logger.debug(f"Disabled user {user.username} in CENSUS")
            
        except Exception as e:
            logger.error(f"Failed to disable user {user.username}: {e}")
            raise
    
    def _is_new_user(self, user: ADUser) -> bool:
        """
        Determine if user is new or existing.
        
        In production, this would query CENSUS database.
        For demo, we'll use a simple heuristic.
        """
        # Simple heuristic: users without recent logon are likely new
        if user.last_logon is None:
            return True
        
        # Users who logged in within last 30 days are likely existing
        cutoff = datetime.utcnow() - timedelta(days=30)
        return user.last_logon < cutoff
    
    async def _update_sync_metadata(self, sync_type: str):
        """Update sync metadata for tracking."""
        try:
            # In production, this would update CENSUS database
            # For demo, we'll just log the metadata
            logger.info(f"Sync metadata updated: {sync_type}")
            
        except Exception as e:
            logger.error(f"Failed to update sync metadata: {e}")
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current AD sync status and metrics."""
        try:
            # In production, this would query CENSUS database
            # For demo, return current metrics
            return {
                "sync_type": "ad_user_sync",
                "last_sync": self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                "metrics": {
                    "total_users": self.metrics.total_users,
                    "processed_users": self.metrics.processed_users,
                    "new_users": self.metrics.new_users,
                    "updated_users": self.metrics.updated_users,
                    "disabled_users": self.metrics.disabled_users,
                    "errors": self.metrics.errors,
                    "duration_minutes": (self.metrics.end_time - self.metrics.start_time).total_seconds() / 60 if self.metrics.end_time else 0
                },
                "ad_server": self.ad_server,
                "domain": self.domain
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close AD connection."""
        if self.connection:
            self.connection.unbind()
            logger.info("AD sync connection closed")

# Global AD sync instance
ad_sync = None

async def get_ad_sync() -> ADSync:
    """Get or create AD sync instance."""
    global ad_sync
    if ad_sync is None:
        ad_server = os.getenv("AD_SERVER", "ldap://ad.company.com")
        bind_user = os.getenv("AD_BIND_USER", "cn=bind,cn=Users,dc=company,dc=com")
        bind_password = os.getenv("AD_BIND_PASSWORD", "bind_password")
        base_dn = os.getenv("AD_BASE_DN", "ou=Users,dc=company,dc=com")
        domain = os.getenv("AD_DOMAIN", "company.com")
        
        ad_sync = ADSync(ad_server, bind_user, bind_password, base_dn, domain)
        await ad_sync.initialize()
    
    return ad_sync

if __name__ == "__main__":
    async def main():
        """Test the AD sync."""
        sync = await get_ad_sync()
        
        try:
            # Run user sync
            metrics = await sync.run_user_sync()
            
            # Print results
            logger.info(f"AD sync completed: {metrics}")
            
            # Get status
            status = await sync.get_sync_status()
            logger.info(f"Current status: {status}")
            
        finally:
            await sync.close()
    
    asyncio.run(main())
