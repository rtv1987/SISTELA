import hashlib
import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .db import data_dir, make_engine
from .dbf_export_api import dbf_export_router
from .grid import active_lines, apply_grid, duplicate_project, owned_line, undo_grid
from .history_api import history_router
from .integration import capabilities
from .lifecycle import lifecycle_router
from .mapping import (
    ApplyMapping,
    ConfirmMapping,
    EntryUpdate,
    apply_suggestion,
    confirm_mapping,
    mark_entry,
    suggestions,
)
from .models import EstimateSection, ImportRun, Project, SourceDocument, utc_now
from .paths import resource_root
from .schemas import (
    GridCommand,
    ImportOut,
    LineCreate,
    LineEdit,
    LineOut,
    ProjectCreate,
    ProjectOut,
)
from .services import ServiceError, add_line, create_project, edit_line, get_project, import_pdf
from .spreadsheets import ExcelExporter, import_xlsx, workbook_preview
from .version import VERSION
from .workflow import workflow_router

MAX_FILE_BYTES = 25 * 1024 * 1024
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
}


class BodyTooLarge(HTTPException):
    def __init__(self):
        super().__init__(413, "Įkėlimo limitas 25 MB.")


class BodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > MAX_FILE_BYTES + 1024 * 1024:  # bounded multipart overhead
                raise BodyTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except BodyTooLarge:
            await JSONResponse({"detail": "Įkėlimo limitas 25 MB."}, status_code=413)(
                scope, receive, send
            )


def create_app(directory: Path | None = None, *, runtime_origin=None, shutdown=None, runtime_token=None, instance_id=None) -> FastAPI:
    directory = directory or data_dir()
    engine = make_engine(directory)
    origins = {runtime_origin} if runtime_origin else ALLOWED_ORIGINS

    @asynccontextmanager
    async def lifespan(app):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        with engine.connect() as connection:
            # No implicit schema creation. A missing migration stops startup with a clear instruction.
            try:
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            except Exception as exc:
                raise RuntimeError("Run: python -m alembic upgrade head") from exc
        with Session(engine) as session:
            session.execute(
                update(ImportRun)
                .where(ImportRun.status == "running")
                .values(
                    status="failed",
                    completed_at=utc_now(),
                    error_message="INTERRUPTED: Importą nutraukė programos sustabdymas.",
                )
            )
            session.commit()
        yield
        engine.dispose()

    app = FastAPI(
        title="SISTELA Assistant", version=VERSION, lifespan=lifespan, docs_url=None, redoc_url=None
    )
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin is not None and origin not in origins:
            return JSONResponse({"detail": "Neleidžiama kilmė."}, status_code=403)
        return await call_next(request)

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status)

    def session_dependency():
        with Session(engine) as session:
            yield session

    app.include_router(lifecycle_router(session_dependency, directory))
    app.include_router(dbf_export_router(session_dependency, directory))
    app.include_router(history_router(session_dependency))
    app.include_router(workflow_router(session_dependency))

    @app.get("/app/info")
    def app_info():
        return {"version": VERSION, "managed": shutdown is not None, "instance_id": instance_id}

    @app.post("/app/logs/open")
    def open_logs():
        if os.name != "nt":
            raise HTTPException(409, "Logų aplanką galima atverti Windows aplinkoje.")
        folder = directory / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder.resolve()))
        return {"opened": True}

    @app.post("/app/quit")
    def quit_app(request: Request, background: BackgroundTasks):
        if shutdown is None:
            raise HTTPException(409, "Šis serveris paleistas kūrėjo režimu.")
        token = request.headers.get("x-sistela-token", "")
        if not (runtime_token and secrets.compare_digest(token, runtime_token)) and request.headers.get("origin") != runtime_origin:
            raise HTTPException(403, "Neleidžiama kilmė.")
        background.add_task(shutdown)
        return {"stopping": True}

    @app.get("/health")
    def health(session: Session = Depends(session_dependency)):
        session.execute(text("SELECT 1"))
        return {"status": "ok", "phase": "0-7", "external_ai": False}

    @app.get("/integration/capabilities")
    def integration_capabilities():
        return capabilities()

    @app.get("/projects/{project_id}/lines/{line_id}/suggestions")
    def mapping_suggestions(project_id: str, line_id: str, session: Session = Depends(session_dependency)):
        return suggestions(session, owned_line(session, project_id, line_id))

    @app.post("/projects/{project_id}/lines/{line_id}/mapping/apply", response_model=LineOut)
    def mapping_apply(project_id: str, line_id: str, data: ApplyMapping, session: Session = Depends(session_dependency)):
        return apply_suggestion(session, project_id, line_id, data)

    @app.post("/projects/{project_id}/lines/{line_id}/mapping/confirm", response_model=LineOut)
    def mapping_confirm(project_id: str, line_id: str, data: ConfirmMapping, session: Session = Depends(session_dependency)):
        return confirm_mapping(session, project_id, line_id, data)

    @app.post("/projects/{project_id}/lines/{line_id}/entry", response_model=LineOut)
    def entry_mark(project_id: str, line_id: str, data: EntryUpdate, session: Session = Depends(session_dependency)):
        return mark_entry(session, project_id, line_id, data)

    @app.post("/xlsx/preview")
    async def xlsx_preview(file: UploadFile, sheet: str = Form(""), header_row: int = Form(0)):
        try:
            data = await file.read(MAX_FILE_BYTES + 1)
            if header_row < 0 or header_row > 10000:
                raise ServiceError(422, "Neteisinga antraštės eilutė.")
            return await run_in_threadpool(workbook_preview, data, sheet or None, header_row or None)
        finally:
            await file.close()

    @app.post("/projects/{project_id}/imports/xlsx", response_model=ImportOut, status_code=201)
    async def xlsx_import(project_id: str, file: UploadFile, sheet: str = Form(...),
            header_row: int = Form(...), mapping: str = Form(...), allow_partial: bool = Form(False),
            session: Session = Depends(session_dependency)):
        try:
            get_project(session, project_id)
            try:
                columns = json.loads(mapping)
                if not isinstance(columns, dict):
                    raise ValueError()
            except ValueError:
                raise ServiceError(422, "Neteisingas kolonų susiejimas.") from None
            data = await file.read(MAX_FILE_BYTES + 1)
            return await run_in_threadpool(import_xlsx, session, directory, project_id,
                file.filename or "import.xlsx", data, sheet, header_row, columns, allow_partial)
        finally:
            await file.close()

    @app.get("/projects/{project_id}/export.xlsx")
    def xlsx_export(project_id: str, session: Session = Depends(session_dependency)):
        project = get_project(session, project_id)
        data, warnings = ExcelExporter().render(project, active_lines(session, project_id),
            {s.id: s.name for s in session.scalars(select(EstimateSection).where(EstimateSection.project_id == project_id))})
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="sistela-assistant.xlsx"',
                     "X-Export-Warnings": str(len(warnings))})

    @app.post("/projects/{project_id}/duplicate", response_model=ProjectOut, status_code=201)
    def project_duplicate(project_id: str, session: Session = Depends(session_dependency)):
        return duplicate_project(session, project_id)

    @app.post("/projects/{project_id}/grid", response_model=list[LineOut])
    def grid_command(project_id: str, command: GridCommand, session: Session = Depends(session_dependency)):
        return apply_grid(session, project_id, command)

    @app.post("/projects/{project_id}/undo", response_model=list[LineOut])
    def grid_undo(project_id: str, session: Session = Depends(session_dependency)):
        return undo_grid(session, project_id)

    @app.post("/projects", response_model=ProjectOut, status_code=201)
    def projects_create(data: ProjectCreate, session: Session = Depends(session_dependency)):
        return create_project(session, data)

    @app.get("/projects", response_model=list[ProjectOut])
    def projects_list(session: Session = Depends(session_dependency)):
        return session.scalars(select(Project).where(Project.deleted_at.is_(None)).order_by(Project.updated_at.desc())).all()

    @app.get("/projects/{project_id}", response_model=ProjectOut)
    def project_get(project_id: str, session: Session = Depends(session_dependency)):
        return get_project(session, project_id)

    @app.get("/projects/{project_id}/lines", response_model=list[LineOut])
    def lines_list(project_id: str, session: Session = Depends(session_dependency)):
        get_project(session, project_id)
        return active_lines(session, project_id)

    @app.post("/projects/{project_id}/lines", response_model=LineOut, status_code=201)
    def lines_create(
        project_id: str, data: LineCreate, session: Session = Depends(session_dependency)
    ):
        return add_line(session, project_id, data)

    @app.put("/projects/{project_id}/lines/{line_id}", response_model=LineOut)
    def lines_edit(
        project_id: str,
        line_id: str,
        data: LineEdit,
        session: Session = Depends(session_dependency),
    ):
        return edit_line(session, project_id, line_id, data)

    @app.post("/projects/{project_id}/imports/pdf", response_model=ImportOut, status_code=201)
    async def pdf_import(
        project_id: str, file: UploadFile, session: Session = Depends(session_dependency)
    ):
        try:
            get_project(session, project_id)
            if not (file.filename or "").lower().endswith(".pdf"):
                raise HTTPException(415, "Pasirinkite PDF failą.")
            data = await file.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise HTTPException(413, "PDF limitas 25 MB.")
            if not data:
                raise HTTPException(422, "Failas tuščias.")
            return await run_in_threadpool(
                import_pdf, session, directory, project_id, file.filename, data
            )
        finally:
            await file.close()

    @app.post("/projects/{project_id}/imports/{run_id}/select/{candidate_id}", response_model=ImportOut)
    def pdf_select(project_id: str, run_id: str, candidate_id: str,
                   session: Session = Depends(session_dependency)):
        get_project(session, project_id)
        run = session.get(ImportRun, run_id)
        if not run or run.project_id != project_id:
            raise HTTPException(404, "Importas nerastas.")
        document = session.get(SourceDocument, run.source_document_id)
        if not document or document.file_type != "pdf":
            raise HTTPException(422, "Tai ne PDF importas.")
        source = directory / "documents" / f"{document.checksum}.pdf"
        if not source.is_file():
            raise HTTPException(409, "Importo šaltinis nepasiekiamas.")
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != document.checksum:
            raise HTTPException(409, "Importo šaltinio kontrolinė suma nesutampa.")
        return import_pdf(session, directory, project_id, document.filename,
                          data, run_id, candidate_id)

    @app.get("/projects/{project_id}/imports", response_model=list[ImportOut])
    def imports_list(project_id: str, session: Session = Depends(session_dependency)):
        get_project(session, project_id)
        return session.scalars(
            select(ImportRun)
            .where(ImportRun.project_id == project_id)
            .order_by(ImportRun.started_at.desc())
        ).all()

    @app.get("/projects/{project_id}/documents")
    def documents_list(project_id: str, session: Session = Depends(session_dependency)):
        get_project(session, project_id)
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "checksum": d.checksum,
                "file_type": d.file_type,
                "page_count": d.page_count,
                "created_at": d.created_at,
            }
            for d in session.scalars(
                select(SourceDocument).where(SourceDocument.project_id == project_id)
            )
        ]

    frontend = resource_root() / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app
