"""add_active_role_to_users

Revision ID: a1b2c3d4e5f6
Revises: 603711be006a
Create Date: 2025-12-14 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '603711be006a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле active_role в таблицу users
    op.add_column('users', sa.Column('active_role', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'active_role')

