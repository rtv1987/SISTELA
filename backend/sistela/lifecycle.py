"""Trash and project-only deletion. Original documents/global knowledge are never removed."""
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import (
    EstimateLine,
    EstimateSection,
    GridChange,
    ImportRun,
    MappingConfirmation,
    Project,
    Requirement,
    SourceDocument,
    utc_now,
)
from .schemas import InputModel, ProjectOut
from .services import ServiceError


def find_project(session, project_id):
    project = session.get(Project, project_id)
    if project is None:
        raise ServiceError(404, "Projektas nerastas.")
    return project


def set_trashed(session, project_id, trashed):
    project = find_project(session, project_id)
    project.deleted_at = utc_now() if trashed else None
    project.updated_at = utc_now()
    session.commit()
    return project


def permanent_delete(session, directory, project_id, confirmation):
    project = find_project(session, project_id)
    if not project.deleted_at:
        raise ServiceError(409, "Pirmiausia perkelkite projektą į šiukšlinę.")
    if confirmation != project.name:
        raise ServiceError(422, "Patvirtinimui įveskite tikslų projekto pavadinimą.")
    documents = list(session.scalars(select(SourceDocument).where(SourceDocument.project_id == project_id)))
    removable = []
    for document in documents:
        # Imported copies are content-addressed and can be shared with other projects.
        references = session.scalar(select(func.count()).select_from(SourceDocument).where(
            SourceDocument.project_id != project_id, SourceDocument.storage_path == document.storage_path))
        root = (directory / "documents").resolve()
        path = root / document.storage_path
        expected = f"{document.checksum}.{document.file_type}"
        if (not references and document.storage_path == expected and Path(expected).name == expected
                and not path.is_symlink() and path.resolve().parent == root):
            removable.append(path)
    # Explicit FK order; reusable SistelaMapping and every Historical* table are untouched.
    for model in (MappingConfirmation, Requirement, GridChange, ImportRun, EstimateLine,
                  EstimateSection, SourceDocument):
        session.execute(delete(model).where(model.project_id == project_id))
    session.delete(project)
    session.commit()
    failed = 0
    for path in removable:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            failed += 1
    return {"deleted": True, "retained_copy_count": failed}


class DeleteProject(InputModel):
    confirmation: str = Field(max_length=200)


def lifecycle_router(session_dependency, directory):
    router = APIRouter()

    @router.get("/trash", response_model=list[ProjectOut])
    def trash(session: Session = Depends(session_dependency)):
        return session.scalars(select(Project).where(Project.deleted_at.is_not(None)).order_by(Project.deleted_at.desc())).all()

    @router.post("/projects/{project_id}/trash", response_model=ProjectOut)
    def move(project_id: str, session: Session = Depends(session_dependency)):
        return set_trashed(session, project_id, True)

    @router.post("/projects/{project_id}/restore", response_model=ProjectOut)
    def restore(project_id: str, session: Session = Depends(session_dependency)):
        return set_trashed(session, project_id, False)

    @router.post("/projects/{project_id}/delete")
    def remove(project_id: str, request: DeleteProject, session: Session = Depends(session_dependency)):
        return permanent_delete(session, directory, project_id, request.confirmation)

    return router
