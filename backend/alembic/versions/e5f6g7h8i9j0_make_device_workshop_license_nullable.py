"""Make devices.workshop_id and license_key nullable for MQTT provisioning

Devices announced via MQTT start as 'pending' — they have no workshop or
license key yet. The original schema incorrectly marked these as NOT NULL,
which silently prevented MQTT-provisioned devices from being saved to the DB.

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allow pending devices (no workshop assigned yet) to be saved
    op.alter_column(
        "devices",
        "workshop_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    # Allow pending devices (no license key yet) to be saved
    op.alter_column(
        "devices",
        "license_key",
        existing_type=sa.String(30),
        nullable=True,
    )


def downgrade() -> None:
    # NOTE: downgrade will fail if any rows have NULL in these columns
    op.alter_column(
        "devices",
        "license_key",
        existing_type=sa.String(30),
        nullable=False,
    )
    op.alter_column(
        "devices",
        "workshop_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
