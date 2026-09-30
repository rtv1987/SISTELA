"""Experimental clone downloads only. No client-supplied server filesystem paths."""
import io
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .dbf_export import DbfExportBlocked, SistelaDbfExporter
from .dbf_project import project_export_plan
from .parsers.dbf import DbfReadError


def dbf_export_router(session_dependency, directory):
    router = APIRouter()

    @router.get("/projects/{project_id}/dbf/plan")
    def plan(project_id: str, session: Session = Depends(session_dependency)):
        return project_export_plan(session, project_id)

    @router.post("/projects/{project_id}/export/dbf")
    def project_export(project_id: str, session: Session = Depends(session_dependency)):
        raise HTTPException(409, detail=project_export_plan(session, project_id))

    @router.post("/dbf/clone")
    async def clone(files: list[UploadFile]):
        try:
            if len(files) != 6:
                raise HTTPException(422, "Pasirinkite visus šešis vieno DBF archyvo failus.")
            payload, size = {}, 0
            for upload in files:
                data = await upload.read(25 * 1024 * 1024 + 1)
                size += len(data)
                if size > 25 * 1024 * 1024:
                    raise HTTPException(413, "Archyvo limitas 25 MB.")
                if upload.filename in payload:
                    raise HTTPException(422, "Pasikartojantis failo vardas.")
                payload[upload.filename or ""] = data
            result = await run_in_threadpool(SistelaDbfExporter(directory).export_clone,
                                            payload, "CLONE_" + uuid4().hex)
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for name in result.generated_filenames + ["manifest.json"]:
                    archive.writestr(name, (Path(result.destination) / name).read_bytes())
            return Response(buffer.getvalue(), media_type="application/zip",
                headers={"Content-Disposition": 'attachment; filename="SISTELA-EXPERIMENTAL-CLONE.zip"',
                         "X-Sistela-Export-Status": "EXPERIMENTAL"})
        except (DbfReadError, DbfExportBlocked) as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            for upload in files:
                await upload.close()

    return router
