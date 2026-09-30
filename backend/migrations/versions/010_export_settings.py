"""Local package settings; no guessed SISTELA parameter values."""
import sqlalchemy as sa
from alembic import op

revision = '010_export_settings'
down_revision = '009_normative_catalog'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('export_settings', sa.Column('key', sa.String(), primary_key=True),
                    sa.Column('value', sa.JSON(), nullable=False))


def downgrade():
    op.drop_table('export_settings')
