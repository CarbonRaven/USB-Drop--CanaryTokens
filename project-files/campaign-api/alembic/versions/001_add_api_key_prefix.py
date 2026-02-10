"""Add api key prefix column for O(1) lookup

Revision ID: 001_add_api_key_prefix
Revises: None
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_add_api_key_prefix"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("key_prefix", sa.String(16), nullable=True))
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_key_prefix", table_name="api_keys")
    op.drop_column("api_keys", "key_prefix")
