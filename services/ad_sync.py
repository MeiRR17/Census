"""
Active Directory Sync - LDAP integration for user data extraction.
Synchronizes user information from Active Directory to CENSUS database.
"""

import asyncio
import logging
from typing import List, Dict, Optional

from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException

from core.config import get_settings


logger = logging.getLogger(__name__)


class ADUser:
    """Data class for Active Directory user information."""
    
    def __init__(self, ad_username: str, full_name: Optional[str] = None, 
                 department: Optional[str] = None, is_active: bool = True):
        self.ad_username = ad_username
        self.full_name = full_name
        self.department = department
        self.is_active = is_active
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "ad_username": self.ad_username,
            "full_name": self.full_name,
            "department": self.department,
            "is_active": self.is_active
        }


class ActiveDirectoryClient:
    """
    LDAP client for Active Directory synchronization.
    Provides async wrapper around synchronous ldap3 operations.
    """
    
    def __init__(self):
        """Initialize AD client with configuration from settings."""
        self.settings = get_settings()
        self.server_url = self.settings.ad_server_url
        self.bind_user = self.settings.ad_bind_user
        self.bind_password = self.settings.ad_bind_password
        self.search_base = self.settings.ad_search_base
        
        # LDAP search filter for user accounts
        self.search_filter = "(&(objectCategory=person)(objectClass=user)(sAMAccountName=*))"
        
        # Attributes to fetch from AD
        self.search_attributes = [
            "sAMAccountName",
            "displayName", 
            "department",
            "userAccountControl",
            "distinguishedName",
            "objectGUID",
            "mail",
            "telephoneNumber",
            "title",
            "physicalDeliveryOfficeName",
            "manager"
        ]
    
    def _is_account_active(self, user_account_control: str) -> bool:
        """
        Determine if AD account is active based on userAccountControl flags.
        
        Args:
            user_account_control: The userAccountControl attribute value from AD
            
        Returns:
            True if account is active, False if disabled
        """
        try:
            uac_int = int(user_account_control)
            # Check if the 2nd bit (0x2) is set - this indicates disabled account
            return (uac_int & 2) == 0
        except (ValueError, TypeError):
            # If we can't parse the value, assume active (safer default)
            logger.warning(f"Invalid userAccountControl value: {user_account_control}")
            return True
    
    def _extract_user_data(self, entry: Dict) -> ADUser:
        """
        Extract user data from LDAP entry.
        
        Args:
            entry: LDAP entry dictionary
            
        Returns:
            ADUser object with extracted data
        """
        attributes = entry.get('attributes', {})
        
        # Extract required fields
        sam_account = attributes.get('sAMAccountName', [''])[0]
        display_name = attributes.get('displayName', [None])[0]
        department = attributes.get('department', [''])[0]
        user_account_control = attributes.get('userAccountControl', ['512'])[0]  # 512 = normal account
        
        # Determine account status
        is_active = self._is_account_active(user_account_control)
        
        # Create user object
        user = ADUser(
            ad_username=sam_account,
            full_name=display_name,
            department=department or "",
            is_active=is_active
        )
        
        logger.debug(f"Extracted AD user: {sam_account} (active: {is_active})")
        return user
    
    def _fetch_users_sync(self) -> List[Dict]:
        """
        Synchronously fetch users from Active Directory.
        
        Returns:
            List of user dictionaries
            
        Raises:
            LDAPException: For LDAP connection or query errors
        """
        logger.info(f"Connecting to AD server: {self.server_url}")
        
        try:
            # Create server and connection objects
            server = Server(self.server_url, get_info=ALL)
            
            # Establish connection
            conn = Connection(
                server,
                user=self.bind_user,
                password=self.bind_password,
                auto_bind=True,
                raise_exceptions=True
            )
            
            logger.info(f"Successfully connected to AD, searching in: {self.search_base}")
            
            # Perform LDAP search
            conn.search(
                search_base=self.search_base,
                search_filter=self.search_filter,
                search_scope=SUBTREE,
                attributes=self.search_attributes,
                size_limit=0  # No limit on results
            )
            
            # Process results
            users = []
            for entry in conn.entries:
                try:
                    # Convert entry to dictionary
                    entry_dict = entry.entry_to_json()
                    import json
                    entry_data = json.loads(entry_dict)
                    
                    # Extract user data
                    user = self._extract_user_data(entry_data)
                    users.append(user.to_dict())
                    
                except Exception as e:
                    logger.warning(f"Failed to process LDAP entry: {e}")
                    continue
            
            conn.unbind()
            logger.info(f"Successfully fetched {len(users)} users from AD")
            return users
            
        except LDAPException as e:
            logger.error(f"LDAP error while fetching users: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching users: {e}")
            raise
    
    async def fetch_all_users_async(self) -> List[Dict]:
        """
        Asynchronously fetch all users from Active Directory.
        
        Returns:
            List of user dictionaries
            
        Note:
            Uses asyncio.to_thread to run synchronous LDAP operations
            in a separate thread to avoid blocking the event loop.
        """
        logger.info("Starting async AD user fetch")
        
        try:
            # Run synchronous LDAP operation in a separate thread
            users = await asyncio.to_thread(self._fetch_users_sync)
            logger.info(f"Async AD fetch completed: {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"Failed to fetch AD users asynchronously: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test connection to Active Directory.
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("Testing AD connection")
        
        try:
            # Run synchronous connection test in separate thread
            result = await asyncio.to_thread(self._test_connection_sync)
            return result
            
        except Exception as e:
            logger.error(f"AD connection test failed: {e}")
            return False
    
    def _test_connection_sync(self) -> bool:
        """
        Synchronously test connection to Active Directory.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            server = Server(self.server_url, get_info=ALL)
            conn = Connection(
                server,
                user=self.bind_user,
                password=self.bind_password,
                auto_bind=True,
                raise_exceptions=False
            )
            
            if conn.bind():
                conn.unbind()
                logger.info("AD connection test successful")
                return True
            else:
                logger.error("AD connection test failed: unable to bind")
                return False
                
        except LDAPException as e:
            logger.error(f"AD connection test failed: {e}")
            return False


# Singleton instance for dependency injection
async def get_ad_client() -> ActiveDirectoryClient:
    """
    Dependency function to get AD client instance.
    
    Usage:
        @app.get("/users")
        async def get_users(ad_client: ActiveDirectoryClient = Depends(get_ad_client)):
            users = await ad_client.fetch_all_users_async()
            return {"users": users}
    """
    return ActiveDirectoryClient()


# Example usage
if __name__ == "__main__":
    import sys
    
    async def main():
        """Test the AD client."""
        client = ActiveDirectoryClient()
        
        # Test connection
        if await client.test_connection():
            print("✅ AD connection successful")
            
            # Fetch users
            try:
                users = await client.fetch_all_users_async()
                print(f"📊 Found {len(users)} users")
                
                # Show first few users
                for i, user in enumerate(users[:5]):
                    print(f"  {i+1}. {user['ad_username']} - {user['full_name']} ({user['department']})")
                    
            except Exception as e:
                print(f"❌ Failed to fetch users: {e}")
        else:
            print("❌ AD connection failed")
    
    # Run the test
    asyncio.run(main())
