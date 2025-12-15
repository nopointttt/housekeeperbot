"""add technician assignments table

Revision ID: c9d8e7f6a5b4
Revises: b7c8d9e0f1a2
Create Date: 2025-12-15 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d8e7f6a5b4'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем таблицу technician_assignments
    op.create_table(
        'technician_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manager_id', sa.BigInteger(), nullable=False),
        sa.Column('technician_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['technician_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_technician_assignments_manager', 'technician_assignments', ['manager_id'])
    op.create_index('ix_technician_assignments_technician', 'technician_assignments', ['technician_id'])
    op.create_unique_constraint('uq_technician_assignments_manager_technician', 'technician_assignments', ['manager_id', 'technician_id'])


def downgrade() -> None:
    op.drop_constraint('uq_technician_assignments_manager_technician', 'technician_assignments', type_='unique')
    op.drop_index('ix_technician_assignments_technician', table_name='technician_assignments')
    op.drop_index('ix_technician_assignments_manager', table_name='technician_assignments')
    op.drop_table('technician_assignments')

