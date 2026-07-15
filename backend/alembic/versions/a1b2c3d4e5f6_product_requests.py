"""product_requests (쫄병 상품 신청)

Revision ID: a1b2c3d4e5f6
Revises: d9fd9506ce0a
Create Date: 2026-07-15 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd9fd9506ce0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.BigInteger(), nullable=False),
        sa.Column('requester_user_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('desired_price', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('reference_url', sa.String(length=500), nullable=True),
        sa.Column(
            'status',
            sa.Enum(
                'pending', 'approved', 'rejected',
                name='productrequeststatus', native_enum=False, length=20,
            ),
            nullable=False,
        ),
        sa.Column('reject_reason', sa.String(length=255), nullable=True),
        sa.Column('product_id', sa.BigInteger(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_product_requests_group_id'), 'product_requests', ['group_id'], unique=False
    )
    op.create_index(
        op.f('ix_product_requests_requester_user_id'),
        'product_requests', ['requester_user_id'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_product_requests_requester_user_id'), table_name='product_requests')
    op.drop_index(op.f('ix_product_requests_group_id'), table_name='product_requests')
    op.drop_table('product_requests')
