"""Add tracking_code to jobs

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tracking_code column to jobs table
    op.add_column(
        "jobs",
        sa.Column("tracking_code", sa.String(6), unique=True, nullable=True)
    )
    
    # Create index for fast lookup
    op.create_index(
        "idx_jobs_tracking_code",
        "jobs",
        ["tracking_code"],
        unique=True
    )


def downgrade() -> None:
    op.drop_index("idx_jobs_tracking_code", table_name="jobs")
    op.drop_column("jobs", "tracking_code")
