#!/usr/bin/env python3
"""
CENSUS DB Integration
==================

Write-through integration for keeping CENSUS database synchronized
with real-time operations from AXLerate Gateway.

This implements Iron Rule 3: Write-Through pattern.
"""

import asyncpg
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class CensusDB:
    """CENSUS Database integration for write-through operations"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("CENSUS DB connection pool initialized")
            await self.create_tables()
        except Exception as e:
            logger.error(f"Failed to initialize CENSUS DB: {e}")
            raise
    
    async def create_tables(self):
        """Create necessary tables if they don't exist"""
        async with self.pool.acquire() as conn:
            try:
                # Devices table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS devices (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        mac_address VARCHAR(17) UNIQUE NOT NULL,
                        device_name VARCHAR(100),
                        device_type VARCHAR(50),
                        model VARCHAR(100),
                        status VARCHAR(20) DEFAULT 'inactive',
                        user_id UUID REFERENCES users(id),
                        location_id UUID REFERENCES locations(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP,
                        firmware_version VARCHAR(50),
                        ip_address INET
                    )
                """)
                
                # Users table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        userid VARCHAR(50) UNIQUE NOT NULL,
                        full_name VARCHAR(200),
                        email VARCHAR(255),
                        department VARCHAR(100),
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Locations table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS locations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        building_name VARCHAR(100) NOT NULL,
                        room_number VARCHAR(50),
                        switch_ip INET,
                        switch_port VARCHAR(50),
                        subnet VARCHAR(50),
                        floor VARCHAR(20),
                        coordinates VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Telephony lines table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS telephony_lines (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        directory_number VARCHAR(50) UNIQUE NOT NULL,
                        partition VARCHAR(100),
                        calling_search_space VARCHAR(100),
                        device_pool VARCHAR(100),
                        route_pattern VARCHAR(100),
                        endpoint_mac VARCHAR(17) REFERENCES devices(mac_address),
                        is_active BOOLEAN DEFAULT true,
                        line_type VARCHAR(50) DEFAULT 'Primary',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Audit log table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        operation VARCHAR(50) NOT NULL,
                        entity_type VARCHAR(50) NOT NULL,
                        entity_id VARCHAR(100) NOT NULL,
                        old_values JSONB,
                        new_values JSONB,
                        user_id UUID REFERENCES users(id),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN DEFAULT true,
                        error_message TEXT
                    )
                """)
                
                # Create indexes for performance
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_userid ON users(userid)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_lines_dn ON telephony_lines(directory_number)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
                
                logger.info("CENSUS DB tables created/verified")
                
            except Exception as e:
                logger.error(f"Failed to create CENSUS tables: {e}")
                raise
    
    async def write_device_operation(self, operation: str, device_data: Dict[str, Any], 
                                user_id: Optional[str] = None):
        """Write device operation to CENSUS DB"""
        async with self.pool.acquire() as conn:
            try:
                if operation == "add_phone":
                    await conn.execute("""
                        INSERT INTO devices (mac_address, device_name, device_type, model, status, created_at)
                        VALUES ($1, $2, $3, $4, 'active', CURRENT_TIMESTAMP)
                        ON CONFLICT (mac_address) DO UPDATE SET
                            device_name = EXCLUDED.device_name,
                            device_type = EXCLUDED.device_type,
                            model = EXCLUDED.model,
                            status = 'active',
                            updated_at = CURRENT_TIMESTAMP
                    """, device_data['mac_address'], device_data.get('device_name'), 
                        device_data.get('device_type'), device_data.get('model'))
                
                elif operation == "update_phone":
                    await conn.execute("""
                        UPDATE devices SET
                            device_name = COALESCE($2, device_name),
                            status = 'updated',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE mac_address = $1
                    """, device_data['mac_address'], device_data.get('device_name'))
                
                elif operation == "delete_phone":
                    await conn.execute("""
                        UPDATE devices SET
                            status = 'deleted',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE mac_address = $1
                    """, device_data['mac_address'])
                
                # Log to audit table
                await self.log_audit(operation, "device", device_data['mac_address'], 
                                None, device_data, user_id, True)
                
                logger.info(f"CENSUS write-through: {operation} for {device_data['mac_address']}")
                
            except Exception as e:
                logger.error(f"CENSUS device write failed: {e}")
                await self.log_audit(operation, "device", device_data.get('mac_address', 'unknown'), 
                                None, device_data, user_id, False, str(e))
                raise
    
    async def write_user_operation(self, operation: str, user_data: Dict[str, Any], 
                               user_id: Optional[str] = None):
        """Write user operation to CENSUS DB"""
        async with self.pool.acquire() as conn:
            try:
                if operation == "add_user":
                    full_name = f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}".strip()
                    await conn.execute("""
                        INSERT INTO users (userid, full_name, email, created_at)
                        VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                        ON CONFLICT (userid) DO UPDATE SET
                            full_name = EXCLUDED.full_name,
                            email = EXCLUDED.email,
                            is_active = true,
                            updated_at = CURRENT_TIMESTAMP
                    """, user_data['userid'], full_name, user_data.get('mailid'))
                
                # Log to audit table
                await self.log_audit(operation, "user", user_data['userid'], 
                                None, user_data, user_id, True)
                
                logger.info(f"CENSUS write-through: {operation} for {user_data['userid']}")
                
            except Exception as e:
                logger.error(f"CENSUS user write failed: {e}")
                await self.log_audit(operation, "user", user_data.get('userid', 'unknown'), 
                                None, user_data, user_id, False, str(e))
                raise
    
    async def write_line_operation(self, operation: str, line_data: Dict[str, Any], 
                              user_id: Optional[str] = None):
        """Write line operation to CENSUS DB"""
        async with self.pool.acquire() as conn:
            try:
                if operation == "add_line":
                    await conn.execute("""
                        INSERT INTO telephony_lines (directory_number, partition, calling_search_space, 
                                              device_pool, route_pattern, line_type, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                        ON CONFLICT (directory_number) DO UPDATE SET
                            partition = EXCLUDED.partition,
                            calling_search_space = EXCLUDED.calling_search_space,
                            device_pool = EXCLUDED.device_pool,
                            route_pattern = EXCLUDED.route_pattern,
                            is_active = true,
                            updated_at = CURRENT_TIMESTAMP
                    """, line_data['pattern'], line_data.get('partition'), 
                        line_data.get('calling_search_space'), line_data.get('device_pool'),
                        line_data.get('route_pattern'), line_data.get('line_type', 'Primary'))
                
                # Log to audit table
                await self.log_audit(operation, "line", line_data['pattern'], 
                                None, line_data, user_id, True)
                
                logger.info(f"CENSUS write-through: {operation} for {line_data['pattern']}")
                
            except Exception as e:
                logger.error(f"CENSUS line write failed: {e}")
                await self.log_audit(operation, "line", line_data.get('pattern', 'unknown'), 
                                None, line_data, user_id, False, str(e))
                raise
    
    async def log_audit(self, operation: str, entity_type: str, entity_id: str,
                      old_values: Optional[Dict], new_values: Optional[Dict],
                      user_id: Optional[str], success: bool, error_message: Optional[str] = None):
        """Log operation to audit table"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_log (operation, entity_type, entity_id, old_values, 
                                     new_values, user_id, success, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, operation, entity_type, entity_id, 
                old_values, new_values, user_id, success, error_message)
    
    async def get_device_status(self, mac_address: str) -> Optional[Dict[str, Any]]:
        """Get current device status from CENSUS"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT mac_address, device_name, device_type, model, status, 
                       created_at, updated_at, last_seen, firmware_version, ip_address
                FROM devices WHERE mac_address = $1
            """, mac_address)
            
            if row:
                return dict(row)
            return None
    
    async def get_user_devices(self, userid: str) -> list:
        """Get all devices associated with a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT d.* FROM devices d
                JOIN users u ON d.user_id = u.id
                WHERE u.userid = $1 AND d.status != 'deleted'
                ORDER BY d.created_at DESC
            """, userid)
            
            return [dict(row) for row in rows]
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("CENSUS DB connection pool closed")

# Singleton instance for the application
census_db = None

async def get_census_db() -> CensusDB:
    """Get CENSUS DB instance"""
    global census_db
    if census_db is None:
        db_url = os.getenv("CENSUS_DB_URL", "postgresql://user:pass@localhost/census")
        census_db = CensusDB(db_url)
        await census_db.initialize()
    return census_db
