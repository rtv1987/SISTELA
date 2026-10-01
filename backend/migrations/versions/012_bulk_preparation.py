"""Equipment rows and searchable average-price material catalogue (derived index only)."""
import sqlalchemy as sa
from alembic import op

revision = '012_bulk_preparation'
down_revision = '011_mapping_row_type'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('estimate_lines', recreate='always', table_args=(
        sa.CheckConstraint("line_type IN ('Material','Work','Equipment','Other')"),
        sa.CheckConstraint("mapping_status IN ('unmapped','suggested','confirmed','rejected','needs_review')"),
        sa.CheckConstraint('source_page IS NULL OR source_page > 0'),
    )):
        pass
    op.execute("""INSERT INTO normative_fts(entry_id,source_id,code,description,category)
        SELECT id,source_id,lower(code),normalized_description,category FROM normative_entries
        WHERE kind='resource_price' AND id NOT IN (SELECT entry_id FROM normative_fts)""")
    op.execute("""UPDATE normative_fts SET description=description || ' ' ||
        (SELECT json_extract(payload,'$.MARKE') FROM normative_entries WHERE id=entry_id)
        WHERE entry_id IN (SELECT id FROM normative_entries
            WHERE json_extract(payload,'$.MARKE') IS NOT NULL)""")


def downgrade():
    raise RuntimeError('Equipment rows must not be discarded; restore a backup instead.')
