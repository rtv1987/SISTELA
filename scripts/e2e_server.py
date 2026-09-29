"""Browser tests use their own disposable database, never the user's projects."""
import tempfile
from pathlib import Path

import uvicorn

from sistela.api import create_app
from sistela.db import ROOT, migrate

if __name__ == '__main__':
    (ROOT / 'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='e2e-', dir=ROOT / 'tmp') as temporary:
        directory = Path(temporary)
        migrate(directory)
        uvicorn.run(create_app(directory), host='127.0.0.1', port=8000)
