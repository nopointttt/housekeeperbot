"""add demo tenant and marketing tables

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2025-12-14 23:59:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users: marketing/profile fields
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("first_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("language_code", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("is_premium", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))

    # requests: tenant_id
    op.add_column(
        "requests",
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index("ix_requests_tenant_id", "requests", ["tenant_id"])

    # complaints: tenant_id
    op.add_column(
        "complaints",
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index("ix_complaints_tenant_id", "complaints", ["tenant_id"])

    # warehouse_items: tenant_id + change uniqueness from name -> (tenant_id, name)
    op.add_column(
        "warehouse_items",
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index("ix_warehouse_items_tenant_id", "warehouse_items", ["tenant_id"])

    # Drop old unique constraint on warehouse_items.name if exists (Postgres default: warehouse_items_name_key)
    try:
        op.drop_constraint("warehouse_items_name_key", "warehouse_items", type_="unique")
    except Exception:
        # If DB uses a different name or already dropped - ignore
        pass

    op.create_unique_constraint("uq_warehouse_items_tenant_name", "warehouse_items", ["tenant_id", "name"])
    op.create_index("ix_warehouse_items_tenant_name", "warehouse_items", ["tenant_id", "name"])

    # user_events table
    op.create_table(
        "user_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_user_events_tenant_id", "user_events", ["tenant_id"])
    op.create_index("ix_user_events_user_id", "user_events", ["user_id"])
    op.create_index("ix_user_events_event_type", "user_events", ["event_type"])
    op.create_index("ix_user_events_created_at", "user_events", ["created_at"])
    op.create_index("ix_user_events_tenant_created", "user_events", ["tenant_id", "created_at"])
    op.create_index("ix_user_events_user_created", "user_events", ["user_id", "created_at"])


def downgrade() -> None:
    # user_events
    op.drop_index("ix_user_events_user_created", table_name="user_events")
    op.drop_index("ix_user_events_tenant_created", table_name="user_events")
    op.drop_index("ix_user_events_created_at", table_name="user_events")
    op.drop_index("ix_user_events_event_type", table_name="user_events")
    op.drop_index("ix_user_events_user_id", table_name="user_events")
    op.drop_index("ix_user_events_tenant_id", table_name="user_events")
    op.drop_table("user_events")

    # warehouse_items
    op.drop_index("ix_warehouse_items_tenant_name", table_name="warehouse_items")
    op.drop_constraint("uq_warehouse_items_tenant_name", "warehouse_items", type_="unique")
    op.drop_index("ix_warehouse_items_tenant_id", table_name="warehouse_items")
    op.drop_column("warehouse_items", "tenant_id")

    # complaints
    op.drop_index("ix_complaints_tenant_id", table_name="complaints")
    op.drop_column("complaints", "tenant_id")

    # requests
    op.drop_index("ix_requests_tenant_id", table_name="requests")
    op.drop_column("requests", "tenant_id")

    # users
    op.drop_column("users", "last_seen_at")
    op.drop_column("users", "first_seen_at")
    op.drop_column("users", "is_premium")
    op.drop_column("users", "language_code")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "username")


