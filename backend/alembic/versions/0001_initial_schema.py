"""Initial baseline schema.

This baseline reflects all models registered against SQLAlchemy metadata at this
point in time. Subsequent schema changes should use `alembic revision --autogenerate`
followed by a hand-tuned migration file (do NOT trust autogenerate for production).

Revision: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    from database import Base
    import models  # noqa: F401 - register all tables
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade():
    from database import Base
    import models  # noqa: F401
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
