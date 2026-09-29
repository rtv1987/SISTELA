from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .history import (
    HistoricalReviewRequest,
    historical_evidence,
    historical_lines,
    import_archive,
    import_summary,
    review_candidates,
)
from .models import HistoricalImport
from .schemas import InputModel, Quantity
from .services import ServiceError
from .units import convert_quantity, unit_compatibility


class ConversionRequest(InputModel):
    quantity: Quantity
    source_unit: str
    target_unit: str


def history_router(session_dependency):
    router = APIRouter()
    DB = Annotated[Session, Depends(session_dependency)]

    @router.get("/history/imports")
    def imports(session: DB):
        return [
            import_summary(session, item)
            for item in session.scalars(
                select(HistoricalImport).order_by(HistoricalImport.imported_at.desc())
            )
        ]

    @router.post("/history/imports")
    async def upload(files: list[UploadFile], session: DB, encoding: str = Form("cp1257")):
        try:
            if len(files) > 6:
                raise ServiceError(422, "Pasirinkite vieno archyvo iki 6 DBF failų.")
            data, size = {}, 0
            from pathlib import PureWindowsPath

            for file in files:
                name = PureWindowsPath(file.filename or "").name
                if not name or name in data:
                    raise ServiceError(422, "Pasikartojantis failo vardas.")
                body = await file.read(25 * 1024 * 1024 + 1)
                size += len(body)
                if size > 25 * 1024 * 1024:
                    raise ServiceError(413, "Viso archyvo įkėlimo limitas 25 MB.")
                data[name] = body
            return await run_in_threadpool(import_archive, session, data, encoding)
        finally:
            for file in files:
                await file.close()

    @router.get("/history/lines")
    def lines(
        session: DB,
        import_id: str | None = None,
        search: str = "",
        system: str = "",
        code: str = "",
        status: str = "",
        limit: int = Query(200, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ):
        return historical_lines(session, import_id, search, system, code, status, limit, offset)

    @router.get("/history/lines/{line_id}/evidence")
    def evidence(line_id: str, session: DB):
        return historical_evidence(session, line_id)

    @router.post("/history/review")
    def review(request: HistoricalReviewRequest, session: DB):
        return review_candidates(session, request)

    @router.post("/units/convert")
    def conversion(request: ConversionRequest):
        try:
            quantity = convert_quantity(
                Decimal(request.quantity), request.source_unit, request.target_unit
            )
        except ValueError as exc:
            raise ServiceError(422, "Šiems vienetams aiškios konversijos taisyklės nėra.") from exc
        return {
            "quantity": str(quantity),
            "compatibility": unit_compatibility(request.source_unit, request.target_unit),
            "applied": False,
        }

    return router
