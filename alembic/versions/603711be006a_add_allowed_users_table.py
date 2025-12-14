"""add_allowed_users_table

Revision ID: 603711be006a
Revises: 997f259e9c03
Create Date: 2025-12-11 00:13:12.177033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '603711be006a'
down_revision: Union[str, None] = '997f259e9c03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем таблицу allowed_users для белого списка сотрудников
    op.create_table('allowed_users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allowed_users_id'), 'allowed_users', ['id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_allowed_users_id'), table_name='allowed_users')
    op.drop_table('allowed_users')

