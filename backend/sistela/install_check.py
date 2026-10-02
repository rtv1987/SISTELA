"""Fail closed on a partial bundle; no application database or user data is opened."""
import hashlib
import importlib
import json
from pathlib import Path


def verify_install(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'INSTALL-MANIFEST.json').read_text(encoding='utf-8'))
    if not manifest:
        raise ValueError('Empty installation manifest')
    for name, digest in manifest.items():
        path = (folder / name).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise ValueError('Missing installation file: ' + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Damaged installation file: ' + name)
    from sqlalchemy import create_engine, text
    from sqlalchemy.util._has_cython import _all_cython_modules
    modules = [m.__name__ for m in _all_cython_modules()]
    for name in modules + ['sqlalchemy.dialects.sqlite.pysqlite', 'alembic.runtime.migration',
                          'uvicorn.loops.asyncio', 'uvicorn.protocols.http.h11_impl', 'uvicorn.lifespan.on']:
        importlib.import_module(name)
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE frozen_check (value INTEGER)'))
        connection.execute(text('INSERT INTO frozen_check VALUES (22)'))
        if connection.scalar(text('SELECT value FROM frozen_check')) != 22:
            raise RuntimeError('Frozen SQLite round-trip failed')
    engine.dispose()
    return modules
