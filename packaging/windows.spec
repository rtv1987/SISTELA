# Build from repository root. Only explicitly listed immutable resources are bundled.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH).parent
datas = [(str(root / 'frontend/dist'), 'frontend/dist'),
         (str(root / 'backend/migrations'), 'backend/migrations'),
         (str(root / 'alembic.ini'), '.'),
         (str(root / 'packaging/END-USER.txt'), '.')]
binaries, hiddenimports = [], []
for package in ('pypdfium2', 'pymupdf', 'rapidfuzz'):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
for package in ('alembic', 'sqlalchemy'):
    datas += copy_metadata(package)
# SQLAlchemy 2.1 has eight distributed *_cy modules. Ship both native modules
# and their upstream Python fallbacks, rather than relying on static analysis.
d, b, h = collect_all('sqlalchemy', filter_submodules=lambda name: '.testing' not in name,
                      exclude_datas=['testing/**'], include_py_files=True)
datas += d
binaries += b
hiddenimports += h

a = Analysis([str(root / 'packaging/windows_launcher.py')], pathex=[str(root / 'backend')],
    binaries=binaries, datas=datas, hiddenimports=hiddenimports + ['uvicorn.loops.asyncio',
    'uvicorn.protocols.http.h11_impl', 'uvicorn.lifespan.on', 'sqlalchemy.dialects.sqlite'],
    excludes=['pytest', 'IPython', 'tkinter', 'matplotlib', 'numpy', 'pandas'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='SISTELA-Assistant',
    debug=False, strip=False, upx=False, console=False, disable_windowed_traceback=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SISTELA-Assistant')
