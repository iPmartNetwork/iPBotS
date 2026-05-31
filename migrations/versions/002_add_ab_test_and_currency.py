"""Add ab_tests table and preferred_currency to users.

Revision ID: 002_ab_test_currency
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa

revision = '002_ab_test_currency'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Create ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('variant_a', sa.Text(), nullable=False),
        sa.Column('variant_b', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('impressions_a', sa.Integer(), server_default='0'),
        sa.Column('impressions_b', sa.Integer(), server_default='0'),
        sa.Column('conversions_a', sa.Integer(), server_default='0'),
        sa.Column('conversions_b', sa.Integer(), server_default='0'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Add preferred_currency to users
    op.add_column(
        'users',
        sa.Column(
            'preferred_currency',
            sa.String(5),
            server_default='IRT',
            nullable=False,
        ),
    )

    # Add new payment methods to enum (PostgreSQL)
    # Note: For PostgreSQL, we need to add new values to the enum type
    op.execute("ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'stripe'")
    op.execute("ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'idpay'")


def downgrade():
    op.drop_column('users', 'preferred_currency')
    op.drop_table('ab_tests')
    # Note: PostgreSQL doesn't support removing enum values easily
