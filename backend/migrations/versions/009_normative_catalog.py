"""Versioned licensed catalog projections and derived offline FTS index."""
import sqlalchemy as sa
from alembic import op

revision = "009_normative_catalog"
down_revision = "008_project_trash"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('normative_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('fingerprint', sa.String(), nullable=False, unique=True),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('imported_at', sa.String(), nullable=False),
        sa.Column('encoding', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('manifest', sa.JSON(), nullable=False),
        sa.Column('diagnostics', sa.JSON(), nullable=False))
    op.create_table('normative_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(), sa.ForeignKey('normative_sources.id'), nullable=False),
        *[sa.Column(n, sa.String(), nullable=False) for n in ('kind','code','unit','unit_id','category','filename')],
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('normalized_description', sa.Text(), nullable=False),
        sa.Column('record_number', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.UniqueConstraint('source_id','filename','record_number'))
    op.create_index('ix_normative_lookup','normative_entries',['source_id','kind','code'])
    op.create_table('normative_relations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(), sa.ForeignKey('normative_sources.id'), nullable=False),
        *[sa.Column(n, sa.String(), nullable=False) for n in ('rate_code','resource_code','kind','filename')],
        sa.Column('amount', sa.String(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('record_number', sa.Integer(), nullable=False))
    op.create_index('ix_normative_relation','normative_relations',['source_id','rate_code'])
    op.execute("CREATE VIRTUAL TABLE normative_fts USING fts5(entry_id UNINDEXED, source_id UNINDEXED, code, description, category, tokenize='unicode61 remove_diacritics 2')")


def downgrade():
    op.execute('DROP TABLE normative_fts')
    op.drop_table('normative_relations')
    op.drop_table('normative_entries')
    op.drop_table('normative_sources')
