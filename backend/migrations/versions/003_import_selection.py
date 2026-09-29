"""Store sheet/column selection separately from diagnostic warnings."""
import sqlalchemy as sa
from alembic import op

revision = "003_import_selection"
down_revision = "002_grid_history"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("import_runs", sa.Column("options", sa.JSON(), nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("import_runs", "options")
