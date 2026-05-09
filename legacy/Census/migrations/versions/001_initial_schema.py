"""Initial schema for CENSUS database

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-04-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create initial CENSUS database schema."""
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('userid', sa.String(length=50), unique=True, nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('manager', sa.String(length=100), nullable=True),
        sa.Column('groups', sa.Text(), nullable=True),
        sa.Column('last_logon', sa.DateTime(timezone=True), nullable=True),
        sa.Column('account_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        # PostgreSQL-specific indexes
        sa.Index('idx_users_userid', 'userid'),
        sa.Index('idx_users_email', 'email'),
        sa.Index('idx_users_department', 'department')
    )
    
    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('building_name', sa.String(length=100), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=True),
        sa.Column('switch_ip', sa.INET(), nullable=True),
        sa.Column('switch_port', sa.String(length=50), nullable=True),
        sa.Column('subnet', sa.String(length=50), nullable=True),
        sa.Column('floor', sa.String(length=20), nullable=True),
        sa.Column('coordinates', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        # PostgreSQL-specific indexes
        sa.Index('idx_locations_building', 'building_name'),
        sa.Index('idx_locations_room', 'room_number')
    )
    
    # Create devices table
    op.create_table('devices',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('mac_address', sa.String(length=17), unique=True, nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), default='inactive', nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('location_id', sa.UUID(), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('firmware_version', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.INET(), nullable=True),
        # PostgreSQL-specific indexes
        sa.Index('idx_devices_mac', 'mac_address'),
        sa.Index('idx_devices_status', 'status'),
        sa.Index('idx_devices_user_status', 'user_id', 'status'),
        sa.Index('idx_devices_location', 'location_id')
    )
    
    # Create telephony_lines table
    op.create_table('telephony_lines',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('directory_number', sa.String(length=50), unique=True, nullable=False),
        sa.Column('partition', sa.String(length=100), nullable=True),
        sa.Column('calling_search_space', sa.String(length=100), nullable=True),
        sa.Column('device_pool', sa.String(length=100), nullable=True),
        sa.Column('route_pattern', sa.String(length=100), nullable=True),
        sa.Column('endpoint_mac', sa.String(length=17), sa.ForeignKey('devices.mac_address'), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('line_type', sa.String(length=50), default='Primary', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        # PostgreSQL-specific indexes
        sa.Index('idx_lines_dn', 'directory_number'),
        sa.Index('idx_lines_partition', 'partition'),
        sa.Index('idx_lines_endpoint', 'endpoint_mac')
    )
    
    # Create audit_log table
    op.create_table('audit_log',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('old_values', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('new_values', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('success', sa.Boolean(), default=True, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        # PostgreSQL-specific indexes
        sa.Index('idx_audit_timestamp', 'timestamp'),
        sa.Index('idx_audit_entity', 'entity_type', 'entity_id')
    )
    
    # Create sync_metadata table
    op.create_table('sync_metadata',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('source_system', sa.String(length=50), unique=True, nullable=False),
        sa.Column('last_sync_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_processed', sa.Integer(), default=0, nullable=False),
        sa.Column('records_updated', sa.Integer(), default=0, nullable=False),
        sa.Column('records_deleted', sa.Integer(), default=0, nullable=False),
        sa.Column('sync_status', sa.String(length=20), default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        # PostgreSQL-specific indexes
        sa.Index('idx_sync_system', 'source_system'),
        sa.Index('idx_sync_status', 'sync_status')
    )

def downgrade():
    """Drop initial CENSUS database schema."""
    
    op.drop_table('sync_metadata')
    op.drop_table('audit_log')
    op.drop_table('telephony_lines')
    op.drop_table('devices')
    op.drop_table('locations')
    op.drop_table('users')
