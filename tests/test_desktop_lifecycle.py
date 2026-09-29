import hashlib
import logging
import sqlite3
import sys

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_workflow import confirm, line, project

from sistela.api import create_app
from sistela.db import database_url, make_engine, migrate
from sistela.desktop import BIND_HOST, InstanceLock, SafeLogFilter, prepare_database, server_config
from sistela.models import SourceDocument
from sistela.paths import ROOT, data_dir, resource_root
from sistela.version import VERSION


@pytest.fixture
def client(tmp_path):
    migrate(tmp_path)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as value:
        yield value


def test_development_and_packaged_paths(monkeypatch, tmp_path):
    monkeypatch.delenv("SISTELA_DATA_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    assert data_dir() == ROOT / "data"
    monkeypatch.setattr(sys, "frozen", True)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert data_dir() == tmp_path / "local/SISTELA Assistant"
    assert resource_root() == tmp_path / "bundle"
    monkeypatch.setenv("SISTELA_DATA_DIR", str(tmp_path / "isolated"))
    assert data_dir() == tmp_path / "isolated"


def test_first_run_migration_and_restart_keep_database(tmp_path):
    assert prepare_database(tmp_path) is None
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        pid = project(client)
    assert prepare_database(tmp_path) is None
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        assert client.get(f"/projects/{pid}").status_code == 200
        assert client.get("/app/info").json()["version"] == VERSION
    assert all(
        (tmp_path / name).is_dir() for name in ("logs", "backups", "documents", "exports", "state")
    )


def test_upgrade_backups_existing_data_before_migration(tmp_path):
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/migrations"))
    config.set_main_option(
        "sqlalchemy.url", database_url(tmp_path).render_as_string().replace("%", "%%")
    )
    command.upgrade(config, "007_estimator_review")
    with sqlite3.connect(tmp_path / "sistela.sqlite3") as db:
        db.execute(
            "INSERT INTO projects(id,name,customer,system_type,status,created_at,updated_at) VALUES('keep','Keep','','GSS','draft','date','date')"
        )
    backup = prepare_database(tmp_path)
    assert backup and backup.is_file()
    with sqlite3.connect(backup) as db:
        assert (
            db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            == "007_estimator_review"
        )
        assert db.execute("SELECT name FROM projects").fetchone()[0] == "Keep"
    with sqlite3.connect(tmp_path / "sistela.sqlite3") as db:
        assert db.execute("SELECT deleted_at FROM projects").fetchone()[0] is None
    assert prepare_database(tmp_path) is None
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1


def test_trash_restore_and_explicit_permanent_confirmation(client):
    pid = project(client)
    row = line(client, pid)
    assert (
        client.post(f"/projects/{pid}/delete", json={"confirmation": "Workflow"}).status_code == 409
    )
    assert client.post(f"/projects/{pid}/trash").json()["deleted_at"]
    assert client.get("/projects").json() == []
    assert client.get("/trash").json()[0]["id"] == pid
    assert client.get(f"/projects/{pid}/lines").status_code == 404
    assert (
        client.post(
            f"/projects/{pid}/lines/{row['id']}/entry", json={"version": 1, "entered": True}
        ).status_code
        == 404
    )
    assert client.post(f"/projects/{pid}/restore").json()["deleted_at"] is None
    assert client.get(f"/projects/{pid}/lines").json()[0]["id"] == row["id"]
    client.post(f"/projects/{pid}/trash")
    assert client.post(f"/projects/{pid}/delete", json={"confirmation": "wrong"}).status_code == 422
    assert client.post(f"/projects/{pid}/delete", json={"confirmation": "Workflow"}).json()[
        "deleted"
    ]
    assert client.get("/trash").json() == []


def test_global_mapping_and_other_project_survive_deletion(client):
    pid = project(client)
    confirm(client, line(client, pid), code="KEEP-NORM")
    other = project(client)
    current = line(client, other)
    client.post(f"/projects/{pid}/trash")
    assert (
        client.post(f"/projects/{pid}/delete", json={"confirmation": "Workflow"}).status_code == 200
    )
    suggestions = client.get(f"/projects/{other}/lines/{current['id']}/suggestions").json()
    assert suggestions[0]["sistela_code"] == "KEEP-NORM"
    assert suggestions[0]["confirmed_count"] == 1


def test_historical_knowledge_survives_permanent_project_delete(client, source_file):
    files = {
        role + "25-04-14.dbf": source_file(role + "25-04-14.dbf").read_bytes()
        for role in ("sd", "dd", "nd")
    }
    assert (
        client.post(
            "/history/imports",
            files=[("files", (name, data)) for name, data in files.items()],
            data={"encoding": "cp1257"},
        ).status_code
        == 200
    )
    historical = client.get("/history/lines?system=GSS&code=N50-270").json()["items"][0]
    client.post(
        "/history/review",
        json={
            "items": [{"id": historical["id"], "version": historical["version"]}],
            "status": "CONFIRMED",
        },
    )
    pid = project(client)
    line(client, pid)
    client.post(f"/projects/{pid}/trash")
    assert (
        client.post(f"/projects/{pid}/delete", json={"confirmation": "Workflow"}).status_code == 200
    )
    assert client.get("/history/lines?status=CONFIRMED").json()["total"] == 1
    assert client.get(f"/history/lines/{historical['id']}/evidence").json()["reviews"]


def test_owned_shared_copies_and_originals(client, tmp_path):
    a, b = project(client), project(client)
    original = tmp_path / "original.pdf"
    original.write_bytes(b"original document")
    checksum = hashlib.sha256(original.read_bytes()).hexdigest()
    documents = tmp_path / "documents"
    documents.mkdir()
    copy = documents / f"{checksum}.pdf"
    copy.write_bytes(original.read_bytes())
    engine = make_engine(tmp_path)
    with Session(engine) as session:
        for pid in (a, b):
            session.add(
                SourceDocument(
                    project_id=pid,
                    filename="original.pdf",
                    file_type="pdf",
                    checksum=checksum,
                    storage_path=copy.name,
                )
            )
        session.commit()
    client.post(f"/projects/{a}/trash")
    client.post(f"/projects/{a}/delete", json={"confirmation": "Workflow"})
    assert copy.exists() and original.exists()
    client.post(f"/projects/{b}/trash")
    client.post(f"/projects/{b}/delete", json={"confirmation": "Workflow"})
    assert not copy.exists() and original.read_bytes() == b"original document"
    engine.dispose()


def test_untrusted_storage_path_is_never_deleted(client, tmp_path):
    pid = project(client)
    original = tmp_path / "original.pdf"
    original.write_bytes(b"keep")
    engine = make_engine(tmp_path)
    with Session(engine) as session:
        session.add(
            SourceDocument(
                project_id=pid,
                filename="original.pdf",
                file_type="pdf",
                checksum="hash",
                storage_path=str(original),
            )
        )
        session.commit()
    client.post(f"/projects/{pid}/trash")
    client.post(f"/projects/{pid}/delete", json={"confirmation": "Workflow"})
    assert original.exists()
    with Session(engine) as session:
        assert not session.scalars(select(SourceDocument)).all()
    engine.dispose()


def test_runtime_binding_origin_version_and_shutdown(tmp_path):
    migrate(tmp_path)
    stopped = []
    app = create_app(
        tmp_path,
        runtime_origin="http://127.0.0.1:54321",
        runtime_token="secret",
        instance_id="test",
        shutdown=lambda: stopped.append(True),
    )
    config = server_config(app, 54321)
    assert config.host == BIND_HOST == "127.0.0.1"
    assert config.reload is False and config.workers == 1 and config.access_log is False
    with TestClient(app, base_url="http://127.0.0.1:54321") as client:
        assert client.get("/app/info").json() == {
            "version": VERSION,
            "managed": True,
            "instance_id": "test",
        }
        assert (
            client.post(
                "/projects",
                json={"name": "Local", "system_type": "GSS"},
                headers={"Origin": "http://127.0.0.1:54321"},
            ).status_code
            == 201
        )
        assert (
            client.post("/app/quit", headers={"Origin": "https://evil.example"}).status_code == 403
        )
        assert client.post("/app/quit").status_code == 403
        assert client.post("/app/quit", headers={"X-Sistela-Token": "secret"}).status_code == 200
        assert stopped == [True]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows instance lock")
def test_single_instance_lock_is_released(tmp_path):
    first, second = (
        InstanceLock(tmp_path / "instance.lock"),
        InstanceLock(tmp_path / "instance.lock"),
    )
    assert first.acquire()
    try:
        assert not second.acquire()
    finally:
        first.close()
    assert second.acquire()
    second.close()


def test_logs_omit_request_error_contents():
    record = logging.LogRecord(
        "uvicorn.error", logging.ERROR, "", 1, "Secret document %s", ("contents",), None
    )
    assert SafeLogFilter().filter(record)
    assert "Secret" not in record.getMessage() and "contents" not in record.getMessage()
