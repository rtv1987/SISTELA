import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path, PureWindowsPath

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .handoff import invalidate_review
from .models import (
    EstimateLine,
    EstimateSection,
    HistoricalLine,
    ImportRun,
    Project,
    SourceDocument,
    utc_now,
)
from .parsers.common import normalize_text, normalize_unit
from .parsers.pdf import PARSER_VERSION, PdfImportError, parse_pdf
from .schemas import LineCreate, LineEdit, ProjectCreate

logger = logging.getLogger(__name__)


class ServiceError(ValueError):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(detail)


def store_document(destination: Path, data: bytes, checksum: str) -> None:
    """Publish a complete file atomically; an interrupted write cannot poison its hash name."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != checksum:
            raise ServiceError(500, "Vietinio šaltinio kontrolinė suma nesutampa.")
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, suffix=".tmp", delete=False
        ) as out:
            temporary = Path(out.name)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def get_project(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if not project or project.deleted_at:
        raise ServiceError(404, "Projektas nerastas.")
    return project


def create_project(session: Session, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def next_order(session: Session, project_id: str) -> int:
    last = session.scalar(
        select(func.max(EstimateLine.sort_order)).where(EstimateLine.project_id == project_id)
    )
    return (last + 1) if last is not None else 0


def add_line(session: Session, project_id: str, data: LineCreate) -> EstimateLine:
    project = get_project(session, project_id)
    values = data.model_dump()
    values["system_type"] = values["system_type"] or project.system_type
    line = EstimateLine(project_id=project_id, sort_order=next_order(session, project_id), **values)
    session.add(line)
    project.status = "NEEDS_REVIEW"
    project.updated_at = utc_now()
    session.commit()
    session.refresh(line)
    return line


def edit_line(session: Session, project_id: str, line_id: str, data: LineEdit) -> EstimateLine:
    get_project(session, project_id)
    line = session.get(EstimateLine, line_id)
    if not line or line.project_id != project_id or line.deleted_at:
        raise ServiceError(404, "Eilutė nerasta.")
    previous_code = line.sistela_code
    previous_candidate = (line.review_data or {}).get("suggestion")
    values = data.model_dump(exclude={"version"})
    # Any semantic edit invalidates a future mapping confirmation without changing its code.
    if any(
        values[k] != getattr(line, k)
        for k in ("project_description", "unit", "system_type", "line_type", "sistela_code", "sistela_original_description")
    ):
        values.update(mapping_status="unmapped", confidence=None)
    invalidate_review(line, values)
    values["entered_at"] = None
    result = session.execute(
        update(EstimateLine)
        .where(
            EstimateLine.id == line_id,
            EstimateLine.project_id == project_id,
            EstimateLine.version == data.version,
        )
        .values(**values, version=data.version + 1, updated_at=utc_now())
    )
    if result.rowcount != 1:
        session.rollback()
        raise ServiceError(409, "Eilutė jau pakeista. Atnaujinkite duomenis prieš išsaugodami.")
    if previous_code != values["sistela_code"]:
        session.flush()
        session.refresh(line)
        from .auto_mapping import learn_code_edit
        learn_code_edit(session, line, previous_code, previous_candidate)
    session.execute(update(Project).where(Project.id == project_id).values(updated_at=utc_now(), status="NEEDS_REVIEW"))
    session.commit()
    session.refresh(line)
    return line


def import_pdf(
    session: Session, directory: Path, project_id: str, filename: str, data: bytes,
    run_id: str | None = None, selected_id: str | None = None,
) -> ImportRun:
    project = get_project(session, project_id)
    checksum = hashlib.sha256(data).hexdigest()
    existing = session.scalar(
        select(SourceDocument).where(
            SourceDocument.project_id == project_id, SourceDocument.checksum == checksum
        )
    )
    if existing and not run_id:
        raise ServiceError(409, "Šis failas jau įkeltas į projektą. Žiūrėkite importo informaciją.")
    destination = directory / "documents" / f"{checksum}.pdf"
    # Immutable content-addressed copy; never use an untrusted client filename as a path.
    store_document(destination, data, checksum)
    document = existing or SourceDocument(
        project_id=project_id,
        filename=PureWindowsPath(filename).name,
        file_type="pdf",
        checksum=checksum,
        storage_path=destination.name,
    )
    if run_id:
        run = session.get(ImportRun, run_id)
        if not run or run.project_id != project_id or not existing or run.source_document_id != existing.id:
            raise ServiceError(404, "Importas nerastas.")
        if not run.options.get("needs_selection") or run.status != "needs_review":
            raise ServiceError(409, "Importo pasirinkimas jau atliktas arba nebegalimas.")
        if run.parser_version != PARSER_VERSION:
            raise ServiceError(409, "Pasikeitė PDF parserio versija. Šį dokumentą reikia analizuoti iš naujo.")
        if selected_id not in {c['id'] for c in run.options.get('diagnostics', []) if c['outcome'] == 'CREDIBLE'}:
            raise ServiceError(422, "Pasirinkite galimą lentelę iš šio importo.")
        claimed = session.execute(update(ImportRun).where(ImportRun.id == run_id,
            ImportRun.status == "needs_review").values(status="running"))
        if claimed.rowcount != 1:
            session.rollback()
            raise ServiceError(409, "Pasirinkimas jau vykdomas.")
        session.commit()
    session.add(document)
    try:
        session.flush()
        if not run_id:
            run = ImportRun(
                project_id=project_id, source_document_id=document.id, parser_version=PARSER_VERSION
            )
        session.add(run)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ServiceError(409, "Šis failas jau įkeltas į projektą.") from None
    run_id, document_id = run.id, document.id
    started = time.perf_counter()
    logger.info("import_start id=%s parser=%s", run_id, PARSER_VERSION)
    try:
        result = parse_pdf(destination, selected_id) if selected_id else parse_pdf(destination)
        document.page_count = result.page_count
        document.extracted_text = result.extracted_text
        run.options = {"needs_selection": result.needs_selection,
                       "diagnostics": result.diagnostics,
                       "selected_candidate": result.schedule.candidate_id if result.schedule else None}
        order = next_order(session, project_id)
        last_section = session.scalar(
            select(func.max(EstimateSection.sort_order)).where(
                EstimateSection.project_id == project_id
            )
        )
        section_order = last_section + 1 if last_section is not None else 0
        sections = {}
        learned = {}
        unknown_texts = {normalize_text(p.project_description) for p in result.lines if p.line_type == "Other"}
        for history in session.scalars(select(HistoricalLine).where(
            HistoricalLine.status == "CONFIRMED", HistoricalLine.system_type == project.system_type,
            HistoricalLine.line_type.in_(["Material", "Work"]),
            HistoricalLine.normalized_description.in_(unknown_texts),
        )):
            key = (history.normalized_description, normalize_unit(history.unit))
            learned.setdefault(key, []).append(history)
        for i, parsed in enumerate(result.lines):
            if parsed.line_type == "Other":
                matches = learned.get((normalize_text(parsed.project_description), normalize_unit(parsed.unit)), [])
                kinds = {h.line_type for h in matches}
                if len(kinds) == 1:
                    parsed.line_type = next(iter(kinds))
                    provenance = json.loads(parsed.source_raw_text)
                    provenance["type_evidence"] = {"origin": "confirmed_history", "ids": [h.id for h in matches]}
                    parsed.source_raw_text = json.dumps(provenance, ensure_ascii=False)
            if parsed.line_type not in sections:
                section = EstimateSection(
                    project_id=project_id,
                    name={"Material": "Medžiagos", "Work": "Montavimo darbai"}.get(parsed.line_type, "Nežinomas tipas – patikrinkite"),
                    sort_order=section_order + len(sections),
                )
                session.add(section)
                session.flush()
                sections[parsed.line_type] = section.id
            line = EstimateLine(
                project_id=project_id,
                section_id=sections[parsed.line_type],
                system_type=project.system_type,
                source_document_id=document_id,
                sort_order=order + i,
                output_description=parsed.project_description,
                sistela_code="", sistela_original_description="",
                **vars(parsed),
            )
            # The same boundary applies to automatic and manual data.
            LineCreate.model_validate({k: getattr(line, k) for k in LineCreate.model_fields})
            session.add(line)
        session.flush()
        from .auto_mapping import populate_automatic
        populate_automatic(session, project_id)
        run.status = "needs_review"
        run.rows_detected = len(result.lines)
        run.pages = result.pages
        run.warnings = result.warnings
        project.status = "IMPORTED"
        project.updated_at = utc_now()
        run.completed_at = utc_now()
        run.elapsed_ms = int((time.perf_counter() - started) * 1000)
        session.commit()
    except Exception as exc:
        session.rollback()  # All parsed lines/sections are discarded together.
        run = session.get(ImportRun, run_id)
        run.status = "failed"
        if isinstance(exc, PdfImportError) and hasattr(exc, 'result'):
            run.options = {"needs_selection": False, "diagnostics": exc.result.diagnostics}
        run.error_message = (
            f"{exc.code}: {exc}"
            if isinstance(exc, PdfImportError)
            else "IMPORT_FAILED: Importo išsaugoti nepavyko."
        )
        run.completed_at = utc_now()
        run.elapsed_ms = int((time.perf_counter() - started) * 1000)
        session.commit()
        logger.warning(
            "import_failed id=%s code=%s elapsed_ms=%s",
            run_id,
            exc.code if isinstance(exc, PdfImportError) else "IMPORT_FAILED",
            run.elapsed_ms,
        )
    session.refresh(run)
    logger.info(
        "import_end id=%s status=%s rows=%s warnings=%s elapsed_ms=%s",
        run.id,
        run.status,
        run.rows_detected,
        len(run.warnings),
        run.elapsed_ms,
    )
    return run
