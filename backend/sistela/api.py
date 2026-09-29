import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .db import data_dir, make_engine
from .grid import active_lines, apply_grid, duplicate_project, owned_line, undo_grid
from .history_api import history_router
from .integration import capabilities
from .mapping import (
    ApplyMapping,
    ConfirmMapping,
    EntryUpdate,
    apply_suggestion,
    confirm_mapping,
    mark_entry,
    suggestions,
)
from .models import ImportRun, Project, SourceDocument, utc_now
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


def create_app(directory: Path | None = None) -> FastAPI:
    directory = directory or data_dir()
    engine = make_engine(directory)

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
        title="SISTELA Assistant", version="0.3.0", lifespan=lifespan, docs_url=None, redoc_url=None
    )
    app.add_middleware(BodyLimitMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(ALLOWED_ORIGINS),
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return JSONResponse({"detail": "Neleidžiama kilmė."}, status_code=403)
        return await call_next(request)

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status)

    def session_dependency():
        with Session(engine) as session:
            yield session

    app.include_router(history_router(session_dependency))

    @app.get("/health")
    def health(session: Session = Depends(session_dependency)):
        session.execute(text("SELECT 1"))
        return {"status": "ok", "phase": "0-6,7-8", "external_ai": False}

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
        data, warnings = ExcelExporter().render(project, active_lines(session, project_id))
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
        return session.scalars(select(Project).order_by(Project.updated_at.desc())).all()

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

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app
