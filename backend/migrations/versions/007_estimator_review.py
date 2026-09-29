"""Persist human review and explicit conversions without changing source quantities."""

import sqlalchemy as sa
from alembic import op

revision = "007_estimator_review"
down_revision = "66611011cc47"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite reflection omits unnamed CHECKs; explicitly restore all three.
    with op.batch_alter_table(
        "estimate_lines",
        recreate="always",
        table_args=(
            sa.CheckConstraint("line_type IN ('Material','Work','Other')"),
            sa.CheckConstraint(
                "mapping_status IN ('unmapped','suggested','confirmed','rejected','needs_review')"
            ),
            sa.CheckConstraint("source_page IS NULL OR source_page > 0"),
        ),
    ) as batch:
        batch.add_column(sa.Column("review_data", sa.JSON(), nullable=False, server_default="{}"))
    with op.batch_alter_table(
        "estimate_lines",
        table_args=(
            sa.CheckConstraint("line_type IN ('Material','Work','Other')"),
            sa.CheckConstraint(
                "mapping_status IN ('unmapped','suggested','confirmed','rejected','needs_review')"
            ),
            sa.CheckConstraint("source_page IS NULL OR source_page > 0"),
        ),
    ) as batch:
        batch.alter_column("review_data", server_default=None)


def downgrade():
    op.execute(
        "UPDATE estimate_lines SET mapping_status='unmapped' WHERE mapping_status IN ('rejected','needs_review')"
    )
    with op.batch_alter_table(
        "estimate_lines",
        recreate="always",
        table_args=(
            sa.CheckConstraint("line_type IN ('Material','Work','Other')"),
            sa.CheckConstraint("mapping_status IN ('unmapped','suggested','confirmed')"),
            sa.CheckConstraint("source_page IS NULL OR source_page > 0"),
        ),
    ) as batch:
        batch.drop_column("review_data")
