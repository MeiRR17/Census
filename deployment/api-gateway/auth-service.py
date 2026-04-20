#!/usr/bin/env python3
"""
API Gateway Authentication Service
=================================

Centralized authentication service for API Gateway.
Manages API keys, rate limiting, and access control.
"""

import os
import asyncio
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import asyncpg

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

@dataclass
class APIKey:
    """API key information."""
    key_id: str
    key_hash: str
    app_name: str
    permissions: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used: Optional[datetime] = None

class APIGatewayAuth:
    """
    API Gateway Authentication Service.
    
    Features:
    - API key generation and validation
    - Rate limiting per application
    - Permission-based access control
    - Centralized logging and monitoring
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
        self.api_keys: Dict[str, APIKey] = {}
    
    async def initialize(self):
        """Initialize authentication service."""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Create tables if they don't exist
            await self.create_tables()
            
            # Load existing API keys
            await self.load_api_keys()
            
            logger.info("API Gateway Auth Service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize auth service: {e}")
            raise
    
    async def create_tables(self):
        """Create necessary tables for authentication."""
        async with self.pool.acquire() as conn:
            try:
                # API keys table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key_id VARCHAR(36) PRIMARY KEY,
                        key_hash VARCHAR(64) UNIQUE NOT NULL,
                        app_name VARCHAR(100) NOT NULL,
                        permissions JSONB NOT NULL,
                        rate_limit INTEGER DEFAULT 100,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_used TIMESTAMP NULL,
                        usage_count INTEGER DEFAULT 0
                    )
                """)
                
                # API usage logs table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_usage_logs (
                        log_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
                        key_id VARCHAR(36) REFERENCES api_keys(key_id),
                        endpoint VARCHAR(255) NOT NULL,
                        method VARCHAR(10) NOT NULL,
                        status_code INTEGER NOT NULL,
                        response_time_ms INTEGER,
                        ip_address INET,
                        user_agent TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
                    CREATE INDEX IF NOT EXISTS idx_api_keys_app_name ON api_keys(app_name);
                    CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);
                    CREATE INDEX IF NOT EXISTS idx_api_usage_logs_key_id ON api_usage_logs(key_id);
                    CREATE INDEX IF NOT EXISTS idx_api_usage_logs_timestamp ON api_usage_logs(timestamp);
                """)
                
                await conn.commit()
                logger.info("Authentication tables created successfully")
                
            except Exception as e:
                await conn.rollback()
                logger.error(f"Failed to create tables: {e}")
                raise
    
    async def load_api_keys(self):
        """Load existing API keys from database."""
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch("""
                    SELECT key_id, key_hash, app_name, permissions, rate_limit,
                           created_at, expires_at, is_active, last_used, usage_count
                    FROM api_keys
                    WHERE is_active = TRUE
                """)
                
                for row in rows:
                    self.api_keys[row['key_hash']] = APIKey(
                        key_id=row['key_id'],
                        key_hash=row['key_hash'],
                        app_name=row['app_name'],
                        permissions=list(row['permissions']),
                        rate_limit=row['rate_limit'],
                        created_at=row['created_at'],
                        expires_at=row['expires_at'],
                        is_active=row['is_active'],
                        last_used=row['last_used'],
                        usage_count=row['usage_count']
                    )
                
                logger.info(f"Loaded {len(self.api_keys)} API keys")
                
            except Exception as e:
                logger.error(f"Failed to load API keys: {e}")
                raise
    
    async def generate_api_key(self, app_name: str, permissions: List[str], 
                           rate_limit: int = 100, expires_days: int = 365) -> str:
        """Generate a new API key."""
        try:
            # Generate API key
            api_key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            key_id = secrets.token_urlsafe(16)
            
            # Set expiration
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Store in database
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO api_keys 
                    (key_id, key_hash, app_name, permissions, rate_limit, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, key_id, key_hash, app_name, permissions, rate_limit, expires_at)
                
                await conn.commit()
            
            # Cache in memory
            self.api_keys[key_hash] = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                app_name=app_name,
                permissions=permissions,
                rate_limit=rate_limit,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True
            )
            
            logger.info(f"Generated API key for {app_name}")
            return api_key
            
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise
    
    async def validate_api_key(self, api_key: str, endpoint: str, 
                           method: str) -> Optional[APIKey]:
        """Validate API key and check permissions."""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Check in cache first
            if key_hash in self.api_keys:
                key_info = self.api_keys[key_hash]
                
                # Check expiration
                if key_info.expires_at and datetime.utcnow() > key_info.expires_at:
                    logger.warning(f"API key expired for {key_info.app_name}")
                    return None
                
                # Check rate limiting
                if not await self.check_rate_limit(key_hash, key_info.rate_limit):
                    logger.warning(f"Rate limit exceeded for {key_info.app_name}")
                    return None
                
                # Check permissions
                if not await self.check_permissions(key_info.permissions, endpoint, method):
                    logger.warning(f"Permission denied for {key_info.app_name}")
                    return None
                
                # Update last used timestamp
                await self.update_last_used(key_hash)
                
                return key_info
            
            # Check in database
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT key_id, key_hash, app_name, permissions, rate_limit,
                           created_at, expires_at, is_active, last_used, usage_count
                    FROM api_keys
                    WHERE key_hash = $1 AND is_active = TRUE
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, key_hash)
                
                if row:
                    key_info = APIKey(
                        key_id=row['key_id'],
                        key_hash=row['key_hash'],
                        app_name=row['app_name'],
                        permissions=list(row['permissions']),
                        rate_limit=row['rate_limit'],
                        created_at=row['created_at'],
                        expires_at=row['expires_at'],
                        is_active=row['is_active'],
                        last_used=row['last_used'],
                        usage_count=row['usage_count']
                    )
                    
                    # Check rate limiting
                    if not await self.check_rate_limit_db(conn, key_hash, key_info.rate_limit):
                        logger.warning(f"Rate limit exceeded for {key_info.app_name}")
                        return None
                    
                    # Check permissions
                    if not await self.check_permissions(key_info.permissions, endpoint, method):
                        logger.warning(f"Permission denied for {key_info.app_name}")
                        return None
                    
                    # Update last used timestamp
                    await self.update_last_used_db(conn, key_hash)
                    
                    # Cache in memory
                    self.api_keys[key_hash] = key_info
                    
                    return key_info
            
            return None
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    async def check_rate_limit(self, key_hash: str, rate_limit: int) -> bool:
        """Check rate limit in memory (simplified)."""
        # In production, use Redis for distributed rate limiting
        # For now, we'll use a simple in-memory check
        return True  # Always allow for now
    
    async def check_rate_limit_db(self, conn, key_hash: str, rate_limit: int) -> bool:
        """Check rate limit in database."""
        try:
            # Count requests in the last minute
            one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
            
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM api_usage_logs
                WHERE key_id = $1 AND timestamp > $2
            """, key_hash, one_minute_ago)
            
            return count < rate_limit
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def check_permissions(self, permissions: List[str], endpoint: str, method: str) -> bool:
        """Check if API key has required permissions."""
        # Define permission mapping
        permission_map = {
            ("/api/telephony/", "GET"): ["telephony:read"],
            ("/api/telephony/", "POST"): ["telephony:write"],
            ("/api/telephony/", "PUT"): ["telephony:write"],
            ("/api/telephony/", "DELETE"): ["telephony:delete"],
            ("/api/census/", "GET"): ["census:read"],
            ("/api/census/", "POST"): ["census:write"],
            ("/api/census/", "PUT"): ["census:write"],
            ("/api/census/", "DELETE"): ["census:delete"],
            ("/superset/", "GET"): ["superset:read"],
        }
        
        # Find required permission
        required_permission = None
        for (pattern, req_method), req_perms in permission_map.items():
            if endpoint.startswith(pattern) and method == req_method:
                required_permission = req_perms[0]
                break
        
        if not required_permission:
            return True  # No specific permission required
        
        return required_permission in permissions
    
    async def update_last_used(self, key_hash: str):
        """Update last used timestamp in memory."""
        if key_hash in self.api_keys:
            self.api_keys[key_hash].last_used = datetime.utcnow()
            self.api_keys[key_hash].usage_count += 1
    
    async def update_last_used_db(self, conn, key_hash: str):
        """Update last used timestamp in database."""
        try:
            await conn.execute("""
                UPDATE api_keys 
                SET last_used = CURRENT_TIMESTAMP, usage_count = usage_count + 1
                WHERE key_hash = $1
            """, key_hash)
            
            await conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to update last used: {e}")
            await conn.rollback()
    
    async def log_api_usage(self, key_id: str, endpoint: str, method: str,
                          status_code: int, response_time_ms: int, 
                          ip_address: str, user_agent: str):
        """Log API usage for monitoring."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO api_usage_logs 
                    (key_id, endpoint, method, status_code, response_time_ms, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, key_id, endpoint, method, status_code, response_time_ms, 
                      ip_address, user_agent)
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
    
    async def get_api_keys(self) -> List[Dict[str, Any]]:
        """Get all API keys."""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT key_id, app_name, permissions, rate_limit, created_at, 
                           expires_at, is_active, last_used, usage_count
                    FROM api_keys
                    ORDER BY created_at DESC
                """)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get API keys: {e}")
            return []
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE api_keys 
                    SET is_active = FALSE
                    WHERE key_id = $1
                """, key_id)
                
                await conn.commit()
                
                # Remove from cache
                for key_hash, key_info in self.api_keys.items():
                    if key_info.key_id == key_id:
                        del self.api_keys[key_hash]
                        break
                
                success = result.split()[-1:][0] if result else "0"
                logger.info(f"API key {key_id} revoked: {success}")
                return success == "1"
                
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            return False
    
    async def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics."""
        try:
            async with self.pool.acquire() as conn:
                # Get usage stats
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_requests,
                        AVG(response_time_ms) as avg_response_time,
                        COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                        COUNT(DISTINCT key_id) as active_keys
                    FROM api_usage_logs
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
                """, days)
                
                # Get top endpoints
                top_endpoints = await conn.fetch("""
                    SELECT endpoint, COUNT(*) as request_count
                    FROM api_usage_logs
                    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
                    GROUP BY endpoint
                    ORDER BY request_count DESC
                    LIMIT 10
                """, days)
                
                return {
                    "period_days": days,
                    "total_requests": stats['total_requests'] if stats else 0,
                    "avg_response_time_ms": float(stats['avg_response_time']) if stats and stats['avg_response_time'] else 0,
                    "error_count": stats['error_count'] if stats else 0,
                    "active_keys": stats['active_keys'] if stats else 0,
                    "top_endpoints": [dict(row) for row in top_endpoints]
                }
                
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {}
    
    async def close(self):
        """Close database connection."""
        if self.pool:
            await self.pool.close()
            logger.info("API Gateway Auth Service shutdown")

# Global auth service instance
auth_service = None

async def get_auth_service() -> APIGatewayAuth:
    """Get or create auth service instance."""
    global auth_service
    if auth_service is None:
        db_url = os.getenv("AUTH_DB_URL", "postgresql://auth_user:auth_password@auth_db:5432/auth_db")
        auth_service = APIGatewayAuth(db_url)
        await auth_service.initialize()
    return auth_service

if __name__ == "__main__":
    async def main():
        """Test the authentication service."""
        auth = await get_auth_service()
        
        try:
            # Generate test API keys
            telephony_key = await auth.generate_api_key(
                "Telephony Management App",
                ["telephony:read", "telephony:write"],
                rate_limit=100
            )
            
            meetings_key = await auth.generate_api_key(
                "Meetings Management App",
                ["census:read", "census:write"],
                rate_limit=50
            )
            
            superset_key = await auth.generate_api_key(
                "Superset Integration",
                ["superset:read"],
                rate_limit=200
            )
            
            print(f"Telephony App Key: {telephony_key}")
            print(f"Meetings App Key: {meetings_key}")
            print(f"Superset App Key: {superset_key}")
            
            # Test validation
            key_info = await auth.validate_api_key(telephony_key, "/api/telephony/devices", "GET")
            print(f"Validation result: {key_info}")
            
            # Get stats
            stats = await auth.get_usage_stats()
            print(f"Usage stats: {stats}")
            
        finally:
            await auth.close()
    
    asyncio.run(main())
