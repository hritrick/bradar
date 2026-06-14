"""Add businesses.source_run_id lineage column (idempotent).

Repairs schema drift on databases that were originally created via
SQLAlchemy `create_all()` before the lineage column was added to the model.

Revision ID: 0002_business_source_run_id
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_business_source_run_id"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns(table)}
    return column in cols


def _has_index(bind, table: str, index_name: str) -> bool:
    insp = inspect(bind)
    return any(ix["name"] == index_name for ix in insp.get_indexes(table))


def _has_fk(bind, table: str, fk_name: str) -> bool:
    insp = inspect(bind)
    return any(fk.get("name") == fk_name for fk in insp.get_foreign_keys(table))


def upgrade():
    bind = op.get_bind()
    # 1) Column
    if not _has_column(bind, "businesses", "source_run_id"):
        op.add_column(
            "businesses",
            sa.Column("source_run_id", sa.String(), nullable=True),
        )
    # 2) Index (idempotent)
    if not _has_index(bind, "businesses", "ix_businesses_source_run_id"):
        op.create_index(
            "ix_businesses_source_run_id",
            "businesses",
            ["source_run_id"],
            unique=False,
        )
    # 3) Foreign key (idempotent) — discovery_source_runs must already exist
    insp = inspect(bind)
    existing_tables = set(insp.get_table_names())
    if "discovery_source_runs" in existing_tables and not _has_fk(
        bind, "businesses", "fk_businesses_source_run_id"
    ):
        op.create_foreign_key(
            "fk_businesses_source_run_id",
            "businesses",
            "discovery_source_runs",
            ["source_run_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    bind = op.get_bind()
    if _has_fk(bind, "businesses", "fk_businesses_source_run_id"):
        op.drop_constraint("fk_businesses_source_run_id", "businesses", type_="foreignkey")
    if _has_index(bind, "businesses", "ix_businesses_source_run_id"):
        op.drop_index("ix_businesses_source_run_id", table_name="businesses")
    if _has_column(bind, "businesses", "source_run_id"):
        op.drop_column("businesses", "source_run_id")
