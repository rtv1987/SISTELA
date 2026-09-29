"""Install/reinstall/uninstall acceptance on this developer PC, with isolated data.

Refuses to touch an existing installation. Temporarily creates the real HKCU
uninstall entry and Start Menu shortcut, then removes them through the uninstaller.
"""
import os
import subprocess
import tempfile
import time
import winreg
from pathlib import Path

import httpx
from smoke_windows import wait_state

from sistela.version import VERSION

ROOT = Path(__file__).resolve().parents[1]


def main():
    keys = [r"Software\SISTELA Assistant",
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SISTELAAssistant"]
    for key in keys:
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ | view):
                    raise RuntimeError("Existing installation detected; refusing installer smoke test")
            except FileNotFoundError:
                pass
    work = Path(tempfile.mkdtemp(prefix="installer-smoke-", dir=ROOT / "tmp"))
    install, data = work / "Application", work / "User data"
    env = {**os.environ, "SISTELA_DATA_DIR": str(data),
           "PATH": os.path.join(os.environ["SystemRoot"], "System32")}
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    options = dict(env=env, cwd=work, creationflags=subprocess.CREATE_NO_WINDOW)
    setup = ROOT / f"dist/windows/SISTELA-Assistant-Setup-{VERSION}.exe"
    exe = install / "SISTELA-Assistant.exe"
    # NSIS /D must be the final, unquoted argument, including when path contains spaces.
    install_command = f'"{setup}" /S /D={install}'
    process = None
    try:
        subprocess.run(install_command, **options, timeout=120, check=True)
        assert exe.is_file() and (install / "Uninstall.exe").is_file()
        shortcut = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/SISTELA Assistant/SISTELA Assistant.lnk"
        assert shortcut.exists()
        process = subprocess.Popen([str(exe), "--no-browser"], **options)
        state = wait_state(data, process)
        with httpx.Client(base_url=state["url"], trust_env=False) as client:
            project = client.post("/projects", json={"name": "Upgrade keeps me", "system_type": "GSS"}).json()
        # Reinstall over a running application: graceful shutdown and preservation.
        subprocess.run(install_command, **options, timeout=120, check=True)
        assert process.wait(timeout=30) == 0
        process = subprocess.Popen([str(exe), "--no-browser"], **options)
        state = wait_state(data, process)
        with httpx.Client(base_url=state["url"], trust_env=False) as client:
            assert client.get(f"/projects/{project['id']}").json()["name"] == "Upgrade keeps me"
        # An unrelated file in the chosen installation folder must not be removed.
        (install / "user-owned.txt").write_text("keep")
        subprocess.run([str(install / "Uninstall.exe"), "/S"], **options, timeout=120, check=True)
        for _ in range(300):
            if not exe.exists() and not shortcut.exists() and not (install / "Uninstall.exe").exists():
                break
            time.sleep(.1)
        assert process.wait(timeout=30) == 0
        assert not exe.exists() and not shortcut.exists()
        assert (install / "user-owned.txt").read_text() == "keep"
        assert (data / "sistela.sqlite3").exists()
        import sqlite3
        with sqlite3.connect(data / "sistela.sqlite3") as connection:
            assert connection.execute("SELECT name FROM projects").fetchone()[0] == "Upgrade keeps me"
        print(f"PASS: actual silent install, shortcut, installed launch, running-app reinstall, preserved DB, uninstall, retained DB and unrelated file. Data: {work}")
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()

