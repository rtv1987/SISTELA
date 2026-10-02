"""Extract the actual release outside the repo; boot twice with a clean environment.

The Python driver observes HTTP only. The child uses solely the extracted bundle.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from contextlib import closing
from pathlib import Path

import httpx
from smoke_windows import wait_state


def clean_environment(data):
    env = {
        k: os.environ[k]
        for k in (
            "SystemRoot",
            "WINDIR",
            "TEMP",
            "TMP",
            "LOCALAPPDATA",
            "APPDATA",
            "USERPROFILE",
            "COMSPEC",
        )
        if k in os.environ
    }
    env.update(PATH=os.path.join(os.environ["SystemRoot"], "System32"), SISTELA_DATA_DIR=str(data))
    return env


def boot(exe, work, data, version):
    options = dict(cwd=work, env=clean_environment(data), creationflags=subprocess.CREATE_NO_WINDOW)
    process = subprocess.Popen([str(exe), "--no-browser"], **options)
    try:
        state = wait_state(data, process)
        with httpx.Client(base_url=state["url"], trust_env=False, timeout=30) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/app/info").json()["version"] == version
            assert "<html" in client.get("/").text.lower()
            projects = client.get("/projects").json()
            if not projects:
                client.post(
                    "/projects", json={"name": "Portable persists", "system_type": "TEST"}
                ).raise_for_status()
            time.sleep(2)
            assert process.poll() is None
            client.post("/app/quit", headers={"X-Sistela-Token": state["token"]}).raise_for_status()
        assert process.wait(timeout=30) == 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("version")
    parser.add_argument("--upgrade-db", type=Path)
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix="sistela-portable-clean-"))
    with zipfile.ZipFile(args.archive) as archive:
        archive.extractall(work / "app")
    exe = work / "app/SISTELA-Assistant/SISTELA-Assistant.exe"
    prior_projects = []
    prior_revision = None
    if args.upgrade_db:
        (work / "data").mkdir()
        with (
            closing(
                sqlite3.connect(args.upgrade_db.resolve().as_uri() + "?mode=ro", uri=True)
            ) as source,
            closing(sqlite3.connect(work / "data/sistela.sqlite3")) as dest,
        ):
            prior_projects = source.execute("SELECT id,name FROM projects ORDER BY id").fetchall()
            prior_revision = source.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            source.backup(dest)
    options = dict(
        cwd=work, env=clean_environment(work / "data"), creationflags=subprocess.CREATE_NO_WINDOW
    )
    subprocess.run([str(exe), "--verify-install"], **options, timeout=60, check=True)
    for _ in range(2):
        boot(exe, work, work / "data", args.version)

    with sqlite3.connect(work / "data/sistela.sqlite3") as connection:
        assert (
            connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            == "012_bulk_preparation"
        )
        if prior_projects:
            assert (
                connection.execute("SELECT id,name FROM projects ORDER BY id").fetchall()
                == prior_projects
            )
            if prior_revision != "012_bulk_preparation":
                assert list((work / "data/backups").glob("before-upgrade-*.sqlite3"))
        else:
            assert (
                connection.execute("SELECT name FROM projects").fetchone()[0] == "Portable persists"
            )
    # Fault-injection in this disposable extraction: every native SQLAlchemy
    # module is unavailable. Its upstream Python fallback must still boot.
    for path in (exe.parent / "_internal/sqlalchemy").rglob("*.pyd"):
        path.rename(path.with_suffix(".disabled"))
    boot(exe, work, work / "fallback-data", args.version)
    # Manifest catches the same incomplete-install failure before success is shown.
    check = subprocess.run([str(exe), "--verify-install"], **options, timeout=60)
    assert check.returncode == 2
    (work / "result.json").write_text(
        json.dumps(
            {
                "version": args.version,
                "launches": 3,
                "health": True,
                "migrations": True,
                "frontend": True,
                "relaunch": True,
                "sqlalchemy_fallback": True,
                "partial_install_detected": True,
            },
            indent=2,
        )
    )
    print(
        "PASS: clean portable, migrations, health, frontend, persistence, relaunch, all SQLAlchemy native modules absent fallback, partial-install rejection. Evidence:",
        work,
    )


if __name__ == "__main__":
    main()
