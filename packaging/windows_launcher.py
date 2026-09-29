"""PyInstaller entry script; never launches a console or a development process."""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from sistela.desktop import entrypoint
    raise SystemExit(entrypoint())
