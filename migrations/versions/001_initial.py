"""Initial migration - tables created by SQLAlchemy create_all.

Revision ID: 001_initial
Create Date: 2026-05-29
"""

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Tables are created by core.database.engine.create_tables()
    # This migration serves as the baseline
    pass


def downgrade():
    pass
