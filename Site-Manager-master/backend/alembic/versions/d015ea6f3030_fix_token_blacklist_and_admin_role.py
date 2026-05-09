"""fix token_blacklist and add admin role

Revision ID: d015ea6f3030
Revises: 72da985a76df
Create Date: 2026-04-22 13:36:26.910069

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd015ea6f3030'
down_revision: Union[str, None] = '72da985a76df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. הוספת ADMIN ל-enum - חייב לרוץ לפני שאר השינויים
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")

    # 2. יצירת טבלת token_blacklist אם היא לא קיימת
    op.create_table('token_blacklist',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )


def downgrade() -> None:
    op.drop_table('token_blacklist')