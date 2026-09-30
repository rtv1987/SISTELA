"""Keep material corrections separate from work norm choices."""
import sqlalchemy as sa
from alembic import op

revision='011_mapping_row_type'
down_revision='010_export_settings'
branch_labels=None
depends_on=None


def upgrade():
    with op.batch_alter_table('sistela_mappings') as table:
        table.add_column(sa.Column('line_type',sa.String(),nullable=False,server_default='Work'))
        table.drop_constraint('uq_mapping_source_unit_code',type_='unique')
        table.create_unique_constraint('uq_mapping_source_unit_code',['system_type','line_type','normalized_source_text','source_unit','sistela_code'])


def downgrade():
    raise RuntimeError('Downgrade would merge independent work/material choices; restore a backup instead.')
