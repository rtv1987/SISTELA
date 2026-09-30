from alembic import context
from sqlalchemy import create_engine

from sistela.db import data_dir, database_url
from sistela.models import Base, ExactDecimal

config = context.config
# Commands invoked with -c alembic.ini honor the same data directory as the app.
url = config.attributes.get("url") or config.get_main_option("sqlalchemy.url")
if url == "sqlite:///data/sistela.sqlite3":
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    url = database_url(directory)


def render_item(kind, obj, autogen_context):
    if kind == "type" and isinstance(obj, ExactDecimal):
        return "sa.Text()"
    return False


def include_object(obj, name, kind, reflected, compare_to):
    # FTS5 virtual tables and their SQLite-maintained shadow tables are explicit DDL.
    return not (kind == 'table' and (name == 'normative_fts' or name.startswith('normative_fts_')))


if context.is_offline_mode():
    context.configure(
        url=url, target_metadata=Base.metadata, literal_binds=True, render_item=render_item
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            render_item=render_item,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
