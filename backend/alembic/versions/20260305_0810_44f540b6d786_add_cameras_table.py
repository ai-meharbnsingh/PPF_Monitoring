"""add_cameras_table

Revision ID: 44f540b6d786
Revises: e5f6g7h8i9j0
Create Date: 2026-03-05 08:10:53.091230+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '44f540b6d786'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('cameras',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workshop_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('camera_type', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('firmware_version', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=False),
        sa.Column('hostname', sa.String(length=100), nullable=True),
        sa.Column('mac_address', sa.String(length=17), nullable=True),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('stream_urls', sa.JSON(), nullable=True),
        sa.Column('mediamtx_config', sa.JSON(), nullable=True),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=100), nullable=True),
        sa.Column('resolutions', sa.JSON(), nullable=True),
        sa.Column('protocols', sa.JSON(), nullable=True),
        sa.Column('has_audio', sa.Boolean(), nullable=False),
        sa.Column('has_ptz', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_online', sa.Boolean(), nullable=False),
        sa.Column('is_assigned', sa.Boolean(), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('discovered_via', sa.String(length=20), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('pit_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pit_id'], ['pits.id']),
        sa.ForeignKeyConstraint(['workshop_id'], ['workshops.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id'),
        sa.UniqueConstraint('pit_id'),
    )


def downgrade() -> None:
    op.drop_table('cameras')
