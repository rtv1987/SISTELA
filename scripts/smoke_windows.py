"""Exercise the frozen application, using isolated data and no development PATH.

Run after build-windows.ps1. This does not substitute for a clean Windows PC test.
"""
import io
import json
import os
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

import httpx
import pefile

from sistela.version import VERSION

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "dist/windows/SISTELA-Assistant/SISTELA-Assistant.exe"


def wait_state(directory, process):
    for _ in range(200):
        if process.poll() is not None:
            raise RuntimeError(f"Packaged process exited: {process.returncode}")
        try:
            return json.loads((directory / "state/runtime.json").read_text())
        except (OSError, ValueError):
            time.sleep(.1)
    raise RuntimeError("Packaged startup timed out; inspect isolated logs")


def main():
    with pefile.PE(str(EXE), fast_load=True) as executable:
        assert executable.FILE_HEADER.Machine == 0x8664  # AMD64
        assert executable.OPTIONAL_HEADER.Subsystem == 2  # Windows GUI, no console
    directory = Path(tempfile.mkdtemp(prefix="packaged-smoke-", dir=ROOT / "tmp"))
    env = {**os.environ, "SISTELA_DATA_DIR": str(directory),
           "PATH": os.path.join(os.environ["SystemRoot"], "System32")}
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    options = dict(env=env, cwd=directory, creationflags=subprocess.CREATE_NO_WINDOW)
    process = subprocess.Popen([str(EXE), "--no-browser"], **options)
    try:
        state = wait_state(directory, process)
        assert state["url"].startswith("http://127.0.0.1:")
        with httpx.Client(base_url=state["url"], trust_env=False, timeout=60) as client:
            assert client.get("/").status_code == 200
            assert client.get("/app/info").json()["version"] == VERSION
            second = subprocess.run([str(EXE), "--no-browser"], **options, timeout=30)
            assert second.returncode == 0
            assert json.loads((directory / "state/runtime.json").read_text())["pid"] == process.pid
            project = client.post("/projects", json={"name": "Packaged GSS", "system_type": "GSS"}).json()
            pid = project["id"]
            pdf = next(p for p in [ROOT / "2024-10-XX-TDP-GSS.pdf", ROOT / "2024-10-XX-TDP-GSS(1).pdf", ROOT / "samples/input/2024-10-XX-TDP-GSS.pdf"] if p.exists())
            response = client.post(f"/projects/{pid}/imports/pdf", files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")})
            response.raise_for_status()
            assert len(client.get(f"/projects/{pid}/lines").json()) == 21
            second_pdf = next(p for p in [ROOT / '2024.07-616SR-BCB-AG.pdf', ROOT / 'samples/input/2024.07-616SR-BCB-AG.pdf'] if p.exists())
            second_project = client.post('/projects', json={'name': 'Packaged second PDF', 'system_type': 'GSS'}).json()['id']
            imported = client.post(f'/projects/{second_project}/imports/pdf', files={'file': (second_pdf.name, second_pdf.read_bytes(), 'application/pdf')})
            imported.raise_for_status()
            second_rows = client.get(f'/projects/{second_project}/lines').json()
            assert len(second_rows) == 12
            assert sum(r['line_type'] == 'Material' for r in second_rows) == 11
            assert sum(r['line_type'] == 'Work' for r in second_rows) == 1
            assert client.get(f"/projects/{pid}/export.xlsx").content[:2] == b"PK"
            files = [next(p for p in [ROOT / f"{role}25-04-14.dbf", ROOT / f"samples/sistela/{role}25-04-14.dbf"] if p.exists()) for role in ("sd", "dd", "nd", "pd", "td", "od")]
            clone = client.post("/dbf/clone", files=[("files", (p.name, p.read_bytes())) for p in files])
            clone.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(clone.content)) as archive:
                assert set(archive.namelist()) == {p.name for p in files} | {"manifest.json"}
                assert all(archive.read(p.name) == p.read_bytes() for p in files)
            assert client.post(f"/projects/{pid}/export/dbf").status_code == 409
            client.post("/history/imports", files=[("files", (p.name, p.read_bytes())) for p in files], data={"encoding": "cp1257"}).raise_for_status()
            historical = client.get("/history/lines", params={"system": "GSS", "code": "N50-270"}).json()["items"][0]
            client.post("/history/review", json={"items": [{"id": historical["id"], "version": historical["version"]}], "status": "CONFIRMED"}).raise_for_status()
            client.post("/app/quit", headers={"X-Sistela-Token": state["token"]}).raise_for_status()
        assert process.wait(timeout=30) == 0
        process = subprocess.Popen([str(EXE), "--no-browser"], **options)
        state = wait_state(directory, process)
        with httpx.Client(base_url=state["url"], trust_env=False, timeout=30) as client:
            assert len(client.get(f"/projects/{pid}/lines").json()) == 21
            assert client.get("/history/lines?status=CONFIRMED").json()["total"] == 1
            client.post(f"/projects/{pid}/trash").raise_for_status()
            assert client.get("/projects").json() == []
            client.post(f"/projects/{pid}/restore").raise_for_status()
            assert client.get("/projects").json()[0]["id"] == pid
            client.post(f"/projects/{pid}/trash").raise_for_status()
            client.post(f"/projects/{pid}/delete", json={"confirmation": "Packaged GSS"}).raise_for_status()
            assert client.get("/history/lines?status=CONFIRMED").json()["total"] == 1
            client.post("/app/quit", headers={"X-Sistela-Token": state["token"]}).raise_for_status()
        assert process.wait(timeout=30) == 0
        print(f"PASS: frozen startup, static UI, single instance, real 21-row PDF, XLSX export, real DBF, experimental clone, project-export gate, restart, trash, restore, delete, retained history. Data: {directory}")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
