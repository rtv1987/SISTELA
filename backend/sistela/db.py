import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return Path(os.environ.get("SISTELA_DATA_DIR", ROOT / "data")).resolve()


def database_url(directory: Path) -> URL:
    return URL.create("sqlite", database=str(directory / "sistela.sqlite3"))


def make_engine(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    engine = create_engine(database_url(directory), connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")

    return engine


def migrate(directory: Path):
    from alembic import command
    from alembic.config import Config

    directory.mkdir(parents=True, exist_ok=True)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/migrations"))
    config.set_main_option(
        "sqlalchemy.url", database_url(directory).render_as_string().replace("%", "%%")
    )
    command.upgrade(config, "head")
