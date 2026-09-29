# ADR 0007 — Windows runtime and project trash

Status: accepted, 2026-09-29. Scope: PHASE 8.

Ship the existing FastAPI/SQLite application as a windowless PyInstaller **onedir**
x64 application. Serve Vite's production assets from the same process and open the
default browser. NSIS produces a per-user installer, Start Menu shortcut, optional
Desktop shortcut and uninstaller. No Electron, embedded browser, development server,
online updater or external runtime installation is necessary.

This reuses the tested architecture and keeps SQLite ownership in one process.
The tradeoff is a browser tab separate from the backend: closing the tab keeps the
application running; the explicit **Uždaryti programą** action stops it. Relaunching
opens the same instance. A file lock belongs to the data directory. A reserved
loopback socket supplies an available port; the instance state has a random identity
and shutdown token. Only the actual local runtime origin is accepted by the managed
API. Access logs and potentially content-bearing third-party exception messages are
excluded from persisted logs.

Resources resolve from PyInstaller's bundle; mutable data resolves independently to
`%LOCALAPPDATA%\SISTELA Assistant`. Development still uses `data/`, and
`SISTELA_DATA_DIR` is an explicit test/developer override. Schema upgrades use Alembic
after a verified SQLite online backup. No downgrade or implicit schema replacement.
Uninstall preserves data and removes only enumerated shipped files, not a recursively
deleted installation directory.

Project deletion uses nullable `Project.deleted_at` (migration 008). Normal project
operations reject trashed projects. Permanent deletion requires the exact project
name and removes project records in foreign-key order. Global mapping/historical
tables are independent and remain. Only content-addressed, unshared document copies
inside the application's document store may be unlinked; original paths are not used.
Shared copies remain until the last referencing project is deleted. File unlink
failures leave a harmless copy and are reported; DB deletion is already committed.

References: [PyInstaller runtime paths](https://www.pyinstaller.org/en/stable/runtime-information.html),
[windowed packaging options](https://pyinstaller.org/en/stable/man/pyinstaller.html),
[NSIS documentation](https://nsis.sourceforge.io/Docs/).
