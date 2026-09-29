"""Transactional grid commands and one-step undo, guarded by row versions."""
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .models import (
    EstimateLine,
    EstimateSection,
    GridChange,
    Project,
    Requirement,
    SourceDocument,
    utc_now,
)
from .schemas import GridCommand, LineCreate
from .services import ServiceError, get_project, next_order


def active_lines(session: Session, project_id: str):
    return session.scalars(select(EstimateLine).where(EstimateLine.project_id == project_id,
        EstimateLine.deleted_at.is_(None)).order_by(EstimateLine.sort_order, EstimateLine.id)).all()


def owned_line(session: Session, project_id: str, line_id: str) -> EstimateLine:
    line = session.get(EstimateLine, line_id)
    if not line or line.project_id != project_id or line.deleted_at:
        raise ServiceError(404, "Eilutė nerasta.")
    return line


def snapshot(line):
    return {c.name: str(getattr(line, c.name)) if isinstance(getattr(line, c.name), Decimal)
            else getattr(line, c.name) for c in EstimateLine.__table__.columns}


def update_versioned(session, line, version, values):
    result = session.execute(update(EstimateLine).where(EstimateLine.id == line.id,
        EstimateLine.version == version).values(**values, version=version + 1, updated_at=utc_now()))
    if result.rowcount != 1:
        raise ServiceError(409, "Duomenys jau pakeisti. Atnaujinkite lentelę.")
    session.flush()
    session.refresh(line)


def apply_grid(session: Session, project_id: str, command: GridCommand):
    get_project(session, project_id)
    ids = [e.id for e in command.edits] + [e.id for e in command.deletes] + [e.id for e in command.duplicates]
    if len(ids) != len(set(ids)):
        raise ServiceError(422, "Eilutė vienoje operacijoje nurodyta kelis kartus.")
    before, versions = {}, {}
    try:
        for edit in command.edits:
            line = owned_line(session, project_id, edit.id)
            before[line.id] = snapshot(line)
            if not set(edit.values) <= LineCreate.model_fields.keys():
                raise ServiceError(422, "Keisti šaltinio ar būsenos laukus draudžiama.")
            full = {k: getattr(line, k) for k in LineCreate.model_fields}
            full.update(edit.values)
            values = LineCreate.model_validate(full).model_dump()
            if any(values[k] != getattr(line, k) for k in ("project_description", "system_type", "unit",
                    "line_type", "sistela_code", "sistela_original_description")):
                values.update(mapping_status="unmapped", confidence=None)
            values["entered_at"] = None
            update_versioned(session, line, edit.version, values)
            versions[line.id] = line.version
        for deletion in command.deletes:
            line = owned_line(session, project_id, deletion.id)
            before[line.id] = snapshot(line)
            update_versioned(session, line, deletion.version, {"deleted_at": utc_now()})
            versions[line.id] = line.version
        order = next_order(session, project_id)
        for i, duplicate in enumerate(command.duplicates):
            original = owned_line(session, project_id, duplicate.id)
            if original.version != duplicate.version:
                raise ServiceError(409, "Eilutė jau pakeista. Atnaujinkite lentelę.")
            values = snapshot(original)
            for key in ("id", "project_id", "created_at", "updated_at", "version"):
                values.pop(key)
            values.update(sort_order=order+i, entered_at=None, mapping_status="unmapped", confidence=None)
            line = EstimateLine(project_id=project_id, **values)
            session.add(line)
            session.flush()
            before[line.id] = None
            versions[line.id] = line.version
        order += len(command.duplicates)
        for i, data in enumerate(command.creates):
            line = EstimateLine(project_id=project_id, sort_order=order+i, **data.model_dump())
            session.add(line)
            session.flush()
            before[line.id] = None
            versions[line.id] = line.version
        if versions:
            session.add(GridChange(project_id=project_id, before=before, after_versions=versions))
            session.execute(update(Project).where(Project.id == project_id).values(updated_at=utc_now()))
        session.commit()
    except ValidationError as exc:
        session.rollback()
        raise ServiceError(422, "Neteisinga eilutės reikšmė. Tikrinkite kiekius, kainas ir privalomus laukus.") from exc
    except Exception:
        session.rollback()
        raise
    return active_lines(session, project_id)


def undo_grid(session: Session, project_id: str):
    get_project(session, project_id)
    change = session.scalar(select(GridChange).where(GridChange.project_id == project_id,
        GridChange.undone.is_(False)).order_by(GridChange.created_at.desc()).limit(1))
    if not change:
        raise ServiceError(409, "Nėra lentelės veiksmo, kurį galima atšaukti.")
    try:
        for line_id, version in change.after_versions.items():
            line = session.get(EstimateLine, line_id)
            old = change.before[line_id]
            if old is None:
                values = {"deleted_at": utc_now(), "entered_at": None}
            else:
                values = {k: v for k, v in old.items() if k not in {"id", "project_id", "version", "created_at", "updated_at"}}
            update_versioned(session, line, version, values)
        change.undone = True
        session.commit()
    except Exception:
        session.rollback()
        raise
    return active_lines(session, project_id)


def duplicate_project(session: Session, project_id: str):
    original = get_project(session, project_id)
    project = Project(name=original.name + " (kopija)", customer=original.customer,
                      system_type=original.system_type)
    session.add(project)
    session.flush()
    documents, sections, line_ids = {}, {}, {}
    for model, index in ((SourceDocument, documents), (EstimateSection, sections)):
        for row in session.scalars(select(model).where(model.project_id == project_id)):
            values = {c.name: getattr(row, c.name) for c in model.__table__.columns
                      if c.name not in {"id", "project_id", "created_at"}}
            copy = model(project_id=project.id, **values)
            session.add(copy)
            session.flush()
            index[row.id] = copy.id
    for row in active_lines(session, project_id):
        values = snapshot(row)
        for key in ("id", "project_id", "created_at", "updated_at", "version"):
            values.pop(key)
        values.update(section_id=sections.get(row.section_id), source_document_id=documents.get(row.source_document_id),
                      entered_at=None, mapping_status="unmapped", confidence=None)
        copy = EstimateLine(project_id=project.id, **values)
        session.add(copy)
        session.flush()
        line_ids[row.id] = copy.id
    for row in session.scalars(select(Requirement).where(Requirement.project_id == project_id)):
        session.add(Requirement(project_id=project.id, related_estimate_line_id=line_ids.get(row.related_estimate_line_id),
            source_document_id=documents.get(row.source_document_id), source_page=row.source_page,
            requirement_text=row.requirement_text, requirement_type=row.requirement_type))
    session.commit()
    session.refresh(project)
    return project
