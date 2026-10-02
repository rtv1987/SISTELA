"""Windowless, single-instance local Windows runtime. No development server."""
import argparse
import ctypes
import json
import logging
import logging.handlers
import os
import re
import secrets
import socket
import sqlite3
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from .paths import data_dir, ensure_data_directories, resource_root
from .version import VERSION

BIND_HOST = "127.0.0.1"


def prepare_database(directory: Path):
    """Online SQLite backup before every pending schema upgrade; fail closed on error."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from .db import migrate
    ensure_data_directories(directory)
    config = Config()
    config.set_main_option("script_location", str(resource_root() / "backend/migrations"))
    head = ScriptDirectory.from_config(config).get_current_head()
    database = directory / "sistela.sqlite3"
    backup = None
    if database.exists() and database.stat().st_size:
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as source:
            version_table = source.execute("SELECT name FROM sqlite_master WHERE name='alembic_version'").fetchone()
            current = source.execute("SELECT version_num FROM alembic_version").fetchone() if version_table else None
            if current and current[0] == head:
                return None
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = directory / "backups" / f"before-upgrade-{stamp}.sqlite3"
            with sqlite3.connect(backup) as destination:
                source.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Database backup verification failed")
    migrate(directory)
    return backup


class InstanceLock:
    def __init__(self, path):
        self.path = path
        self.file = None

    def acquire(self):
        import msvcrt
        self.file = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            self.file.close()
            self.file = None
            return False

    def close(self):
        if self.file:
            import msvcrt
            self.file.seek(0)
            msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            self.file.close()
            self.file = None


def local_request(url, token=None):
    if not re.fullmatch(r"http://127\.0\.0\.1:\d+/(app/info|app/quit)", url):
        raise ValueError("Only the local runtime may be contacted")
    request = urllib.request.Request(url, data=b"{}" if token else None,
        headers={"Content-Type": "application/json", **({"X-Sistela-Token": token} if token else {})})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=1) as response:
        return json.load(response)


def existing_instance(directory):
    try:
        state = json.loads((directory / "state/runtime.json").read_text(encoding="utf-8"))
        if local_request(state["url"] + "/app/info").get("instance_id") == state["instance_id"]:
            return state
    except (OSError, ValueError, KeyError):
        pass
    return None


class SafeLogFilter(logging.Filter):
    def filter(self, record):
        # Request traces/SQL errors can contain parameters. Never store their contents.
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        if not record.name.startswith("sistela."):
            record.msg, record.args = "Runtime event (request content omitted)", ()
        return True


def configure_logs(directory):
    handler = logging.handlers.RotatingFileHandler(directory / "logs/application.log",
        maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.addFilter(SafeLogFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


def server_config(app, port):
    import uvicorn
    return uvicorn.Config(app, host=BIND_HOST, port=port, reload=False, workers=1,
        loop="asyncio", http="h11", ws="none", log_config=None, access_log=False)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true", help="Packaging smoke tests only")
    parser.add_argument("--shutdown", action="store_true", help="Gracefully close this user's instance")
    args = parser.parse_args(argv)
    directory = data_dir()
    ensure_data_directories(directory)
    if args.shutdown:
        state = existing_instance(directory)
        if state:
            local_request(state["url"] + "/app/quit", state["token"])
            for _ in range(100):
                if not existing_instance(directory):
                    return 0
                time.sleep(.1)
            return 1
        return 0
    lock = InstanceLock(directory / "state/instance.lock")
    if not lock.acquire():
        for _ in range(200):
            state = existing_instance(directory)
            if state:
                if not args.no_browser:
                    webbrowser.open(state["url"])
                return 0
            time.sleep(.1)
        raise RuntimeError("Existing application is still starting")
    state_file = directory / "state/runtime.json"
    sock = None
    try:
        configure_logs(directory)
        prepare_database(directory)
        import uvicorn

        from .api import create_app
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((BIND_HOST, 0))  # Reserve an OS-selected free port, never a guessed fixed port.
        port = sock.getsockname()[1]
        url = f"http://{BIND_HOST}:{port}"
        instance_id, token = secrets.token_hex(16), secrets.token_hex(32)
        server = None

        def stop():
            server.should_exit = True

        app = create_app(directory, runtime_origin=url, shutdown=stop,
            runtime_token=token, instance_id=instance_id)
        server = uvicorn.Server(server_config(app, port))

        def ready():
            while not server.started and not server.should_exit:
                time.sleep(.05)
            if not server.started:
                return
            temporary = state_file.with_suffix(".tmp")
            temporary.write_text(json.dumps(dict(url=url, pid=os.getpid(), instance_id=instance_id,
                token=token, version=VERSION)), encoding="utf-8")
            temporary.replace(state_file)
            logging.getLogger("sistela.desktop").info("application_started version=%s", VERSION)
            if not args.no_browser:
                webbrowser.open(url)

        threading.Thread(target=ready, daemon=True).start()
        server.run(sockets=[sock])
        return 0
    finally:
        state_file.unlink(missing_ok=True)
        if sock:
            sock.close()
        lock.close()


def entrypoint():
    try:
        return main()
    except Exception as exc:
        logging.getLogger("sistela.desktop").error("startup_failed type=%s", type(exc).__name__)
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(None,
                "SISTELA Assistant nepavyko paleisti. Duomenys neištrinti.\n"
                "Patikrinkite vietą diske ir logų aplanką:\n" + str(data_dir() / "logs"),
                "SISTELA Assistant", 0x10)
        return 1
