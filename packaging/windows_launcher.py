"""PyInstaller entry script; never launches a console or a development process."""
import multiprocessing
import sys
from pathlib import Path

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if '--verify-install' in sys.argv:
        from sistela.install_check import verify_install
        try:
            verify_install(Path(sys.executable).parent)
        except Exception:
            raise SystemExit(2) from None
        raise SystemExit(0)
    from sistela.desktop import entrypoint
    raise SystemExit(entrypoint())
