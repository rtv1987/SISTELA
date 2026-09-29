"""Project trash is reversible; global knowledge remains independent."""
import sqlalchemy as sa
from alembic import op

revision = "008_project_trash"
down_revision = "007_estimator_review"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("projects", sa.Column("deleted_at", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("projects") as batch:
        batch.drop_column("deleted_at")
