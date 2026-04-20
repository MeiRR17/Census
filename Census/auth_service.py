#!/usr/bin/env python3
"""
Service-to-Service Authentication
================================

Secure authentication between microservices using API keys.
Handles service registration, key rotation, and token validation.
"""

import asyncio
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceRegistration:
    """Service registration information."""
    service_name: str
    service_url: str
    api_key: str
    expires_at: datetime
    permissions: list = None

class AuthService:
    """
    Service-to-Service authentication manager.
    
    Features:
    - Service registration and management
    - API key generation and validation
    - Token rotation and security
    - Service discovery and health checks
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
        self.registered_services: Dict[str, ServiceRegistration] = {}
    
    async def initialize(self):
        """Initialize authentication service."""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Auth Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Auth Service: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def register_service(self, service_name: str, service_url: str, 
                        permissions: list = None) -> str:
        """
        Register a new service and generate API key.
        
        Args:
            service_name: Name of the service
            service_url: URL of the service
            permissions: List of permissions for the service
        
        Returns:
            Generated API key
        """
        try:
            # Generate secure API key
            api_key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Set expiration (90 days)
            expires_at = datetime.utcnow() + timedelta(days=90)
            
            # Store registration
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO service_registrations (
                        service_name, service_url, api_key, key_hash,
                        permissions, expires_at, created_at, status
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, 'active'
                    )
                """, service_name, service_url, api_key, key_hash,
                    permissions, expires_at)
            
            # Cache registration
            registration = ServiceRegistration(
                service_name=service_name,
                service_url=service_url,
                api_key=api_key,
                expires_at=expires_at,
                permissions=permissions or []
            )
            
            self.registered_services[api_key] = registration
            
            logger.info(f"Service registered: {service_name}")
            return api_key
            
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {e}")
            raise
    
    async def validate_token(self, api_key: str) -> Optional[ServiceRegistration]:
        """
        Validate API key and return service registration.
        
        Args:
            api_key: API key to validate
        
        Returns:
            Service registration if valid, None otherwise
        """
        try:
            # Check cache first
            if api_key in self.registered_services:
                registration = self.registered_services[api_key]
                
                # Check expiration
                if datetime.utcnow() > registration.expires_at:
                    logger.warning(f"API key expired for {registration.service_name}")
                    del self.registered_services[api_key]
                    return None
                
                return registration
            
            # Check database
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT service_name, service_url, permissions, expires_at, status
                    FROM service_registrations 
                    WHERE api_key = $1 AND status = 'active'
                """, hashlib.sha256(api_key.encode()).hexdigest())
                
                if result:
                    registration = ServiceRegistration(
                        service_name=result['service_name'],
                        service_url=result['service_url'],
                        api_key=api_key,
                        expires_at=result['expires_at'],
                        permissions=result['permissions']
                    )
                    
                    # Cache the result
                    self.registered_services[api_key] = registration
                    
                    return registration
            
            return None
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    async def revoke_token(self, api_key: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key: API key to revoke
        
        Returns:
            True if revoked successfully
        """
        try:
            # Remove from cache
            if api_key in self.registered_services:
                del self.registered_services[api_key]
            
            # Update database
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE service_registrations 
                    SET status = 'revoked', updated_at = CURRENT_TIMESTAMP
                    WHERE key_hash = $1
                """, hashlib.sha256(api_key.encode()).hexdigest())
            
            success = result.split()[-1:][0] if result else "0"
            
            if success == "1":
                logger.info(f"API key revoked successfully")
                return True
            else:
                logger.warning("API key not found for revocation")
                return False
                
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False
    
    async def rotate_key(self, old_api_key: str) -> str:
        """
        Rotate API key for a service.
        
        Args:
            old_api_key: Old API key to rotate
        
        Returns:
            New API key
        """
        try:
            # Get service registration
            registration = await self.validate_token(old_api_key)
            if not registration:
                raise ValueError("Invalid API key")
            
            # Revoke old key
            await self.revoke_token(old_api_key)
            
            # Generate new key
            new_api_key = await self.register_service(
                registration.service_name,
                registration.service_url,
                registration.permissions
            )
            
            logger.info(f"API key rotated for {registration.service_name}")
            return new_api_key
            
        except Exception as e:
            logger.error(f"API key rotation failed: {e}")
            raise
    
    async def get_service_health(self, api_key: str) -> Dict[str, Any]:
        """
        Get health status of a service.
        
        Args:
            api_key: API key of the service
        
        Returns:
            Service health information
        """
        try:
            registration = await self.validate_token(api_key)
            if not registration:
                return {"error": "Invalid API key"}
            
            # Check service health
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{registration.service_url}/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            return {
                                "service_name": registration.service_name,
                                "service_url": registration.service_url,
                                "status": "healthy",
                                "last_check": datetime.utcnow().isoformat(),
                                "health_data": health_data
                            }
                        else:
                            return {
                                "service_name": registration.service_name,
                                "service_url": registration.service_url,
                                "status": "unhealthy",
                                "http_status": response.status,
                                "last_check": datetime.utcnow().isoformat()
                            }
                            
                except asyncio.TimeoutError:
                    return {
                        "service_name": registration.service_name,
                        "service_url": registration.service_url,
                        "status": "timeout",
                        "error": "Service health check timeout"
                    }
                    
        except Exception as e:
            logger.error(f"Service health check failed: {e}")
            return {
                "service_name": registration.service_name,
                "service_url": registration.service_url,
                "status": "error",
                "error": str(e)
            }
    
    async def get_registered_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        try:
            async with self.pool.acquire() as conn:
                services = await conn.fetch("""
                    SELECT service_name, service_url, expires_at, status
                    FROM service_registrations 
                    WHERE status = 'active'
                    ORDER BY created_at DESC
                """)
                
                return {
                    "services": [dict(service) for service in services],
                    "total_count": len(services),
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get registered services: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_keys(self):
        """Clean up expired API keys."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE service_registrations 
                    SET status = 'expired', updated_at = CURRENT_TIMESTAMP
                    WHERE expires_at < CURRENT_TIMESTAMP AND status = 'active'
                """)
                
                expired_count = result.split()[-1:][0] if result else "0"
                logger.info(f"Cleaned up {expired_count} expired API keys")
                
                # Remove from cache
                keys_to_remove = []
                for api_key, registration in self.registered_services.items():
                    if datetime.utcnow() > registration.expires_at:
                        keys_to_remove.append(api_key)
                
                for key in keys_to_remove:
                    del self.registered_services[key]
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Auth Service shutdown")

# Global auth service instance
auth_service = None

async def get_auth_service() -> AuthService:
    """Get or create auth service instance."""
    global auth_service
    if auth_service is None:
        db_url = os.getenv("CENSUS_DB_URL", "postgresql://census_user:census_password@localhost:5432/census_db")
        auth_service = AuthService(db_url)
        await auth_service.initialize()
    return auth_service

if __name__ == "__main__":
    async def main():
        """Test the auth service."""
        auth = await get_auth_service()
        
        try:
            # Register a test service
            api_key = await auth.register_service(
                "test-service",
                "http://localhost:8002",
                ["read", "write"]
            )
            
            print(f"Registered service with API key: {api_key}")
            
            # Validate the key
            registration = await auth.validate_token(api_key)
            print(f"Validation result: {registration}")
            
            # Get service health
            health = await auth.get_service_health(api_key)
            print(f"Service health: {health}")
            
            # Get all services
            services = await auth.get_registered_services()
            print(f"Registered services: {services}")
            
        finally:
            await auth.close()
    
    asyncio.run(main())
