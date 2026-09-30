import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from .models import NormativeCatalogSource, NormEntry, NormRelation
from .normative import entry_out, ingest_folder, ingest_zip, search_catalog, source_out
from .schemas import InputModel, LineOut
from .services import ServiceError


class CatalogFolder(InputModel):
    path: str


class CatalogChoice(InputModel):
    entry_id: str
    version: int


def normative_router(session_dependency):
    router = APIRouter()

    @router.get('/normative/sources')
    def sources(session=Depends(session_dependency)):
        return [source_out(s) for s in session.scalars(select(NormativeCatalogSource).order_by(NormativeCatalogSource.imported_at.desc()))]

    @router.post('/normative/folder')
    def folder(data: CatalogFolder, session=Depends(session_dependency)):
        return ingest_folder(session, Path(data.path))

    @router.post('/normative/zip')
    async def zip_import(file: UploadFile, session=Depends(session_dependency)):
        try:
            with tempfile.TemporaryDirectory(prefix='sistela-upload-') as temp:
                path = Path(temp)/'source.zip'
                total = 0
                with path.open('wb') as out:
                    while chunk := await file.read(1024*1024):
                        total += len(chunk)
                        if total > 150*1024*1024:
                            raise ServiceError(413, 'ZIP limitas 150 MB.')
                        out.write(chunk)
                return await run_in_threadpool(ingest_zip, session, path, Path(file.filename or 'ZIP').name)
        finally:
            await file.close()

    @router.get('/normative/search')
    def search(q: str='', kind: str='rate', unit: str='', category: str='', session=Depends(session_dependency)):
        return search_catalog(session,q,kind,unit,category)

    @router.get('/normative/entries/{entry_id}')
    def detail(entry_id: str, session=Depends(session_dependency)):
        entry = session.get(NormEntry,entry_id)
        if not entry:
            raise ServiceError(404,'Normatyvas nerastas.')
        relations = session.scalars(select(NormRelation).where(NormRelation.source_id==entry.source_id,NormRelation.rate_code==entry.code)).all()
        return {**entry_out(entry), 'payload':entry.payload, 'relations':[
            {k:getattr(r,k) for k in ('kind','resource_code','amount','resolved','filename','record_number')} for r in relations]}
    @router.post('/projects/{project_id}/automatic', response_model=list[LineOut])
    def automatic(project_id: str, session=Depends(session_dependency)):
        from .auto_mapping import populate_automatic
        from .grid import active_lines
        populate_automatic(session, project_id)
        session.commit()
        return active_lines(session, project_id)

    @router.post('/projects/{project_id}/lines/{line_id}/catalog', response_model=LineOut)
    def choose(project_id: str, line_id: str, request: CatalogChoice, session=Depends(session_dependency)):
        from .auto_mapping import choose_catalog
        return choose_catalog(session, project_id, line_id, request.entry_id, request.version)
    return router
