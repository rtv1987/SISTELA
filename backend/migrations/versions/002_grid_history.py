"""Grid undo, entry progress and confirmed mapping provenance."""
import sqlalchemy as sa
from alembic import op

revision = "002_grid_history"
down_revision = "231609db4375"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("estimate_lines", sa.Column("deleted_at", sa.String(), nullable=True))
    op.add_column("estimate_lines", sa.Column("entered_at", sa.String(), nullable=True))
    with op.batch_alter_table("sistela_mappings", naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"},
                             table_args=[sa.CheckConstraint("usage_count >= 0 AND confirmed_count >= 0", name="ck_mapping_counts")]) as batch:
        batch.add_column(sa.Column("source_unit", sa.String(), nullable=False, server_default=""))
        batch.drop_constraint("uq_sistela_mappings_system_type", type_="unique")
        batch.create_unique_constraint("uq_mapping_source_unit_code",
                                       ["system_type", "normalized_source_text", "source_unit", "sistela_code"])
    op.create_table("grid_changes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("before", sa.JSON(), nullable=False), sa.Column("after_versions", sa.JSON(), nullable=False),
        sa.Column("undone", sa.Boolean(), nullable=False), sa.Column("created_at", sa.String(), nullable=False))
    op.create_index("ix_grid_changes_project_id", "grid_changes", ["project_id"])
    op.create_table("mapping_confirmations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mapping_id", sa.String(36), sa.ForeignKey("sistela_mappings.id"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("line_id", sa.String(36), sa.ForeignKey("estimate_lines.id"), nullable=False),
        sa.Column("previous_code", sa.String(), nullable=False), sa.Column("selected_code", sa.String(), nullable=False),
        sa.Column("source_text", sa.String(), nullable=False), sa.Column("created_at", sa.String(), nullable=False))


def downgrade():
    # Returning to the old uniqueness could lose distinct unit histories; refuse rather than delete.
    connection = op.get_bind()
    duplicates = connection.execute(sa.text("SELECT 1 FROM sistela_mappings GROUP BY system_type, normalized_source_text, sistela_code HAVING COUNT(*) > 1 LIMIT 1")).first()
    if duplicates:
        raise RuntimeError("Cannot downgrade distinct unit histories without data loss")
    op.drop_table("mapping_confirmations")
    op.drop_index("ix_grid_changes_project_id", table_name="grid_changes")
    op.drop_table("grid_changes")
    with op.batch_alter_table("sistela_mappings") as batch:
        batch.drop_constraint("uq_mapping_source_unit_code", type_="unique")
        batch.drop_column("source_unit")
        batch.create_unique_constraint("uq_sistela_mappings_system_type", ["system_type", "normalized_source_text", "sistela_code"])
    op.drop_column("estimate_lines", "entered_at")
    op.drop_column("estimate_lines", "deleted_at")
