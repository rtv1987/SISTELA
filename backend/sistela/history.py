"""Local historical knowledge; reviews are independent of current estimate prices."""

import json
import logging
import tempfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field
from rapidfuzz.fuzz import ratio
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from .models import HistoricalEstimate, HistoricalImport, HistoricalLine, HistoricalReview, utc_now
from .parsers.common import normalize_text
from .parsers.dbf import DbfReadError, read_dbf
from .parsers.historical_dbf import VERSION, detect_archive, reconstruct
from .schemas import InputModel
from .services import ServiceError
from .units import unit_compatibility

logger = logging.getLogger("sistela.history")


class ReviewItem(InputModel):
    id: str
    version: int = Field(ge=1)
    system_type: str | None = Field(default=None, min_length=1, max_length=100)


class HistoricalReviewRequest(InputModel):
    items: list[ReviewItem] = Field(min_length=1, max_length=500)
    status: Literal["CONFIRMED", "REJECTED"]
    acknowledge_ambiguity: bool = False


def import_archive(session, files: dict[str, bytes], encoding: str):
    if encoding not in {"cp1257", "cp1252", "utf-8"}:
        raise ServiceError(422, "Pasirinkite cp1257, cp1252 arba utf-8 koduotę.")
    try:
        roles, checksum = detect_archive(files)
        existing = session.scalar(
            select(HistoricalImport).where(HistoricalImport.source_hash == checksum)
        )
        if existing:
            if existing.encoding != encoding:
                raise ServiceError(
                    409, "Šis archyvas jau importuotas kita koduote. Esami duomenys nepakeisti."
                )
            return import_summary(session, existing) | {"duplicate": True}
        with tempfile.TemporaryDirectory(prefix="sistela-history-") as directory:
            tables = {}
            for role, metadata in roles.items():
                path = Path(directory) / metadata["name"]
                path.write_bytes(
                    files[metadata["name"]]
                )  # Unmodified upload copy, never an original path.
                tables[role] = read_dbf(path, encoding=encoding)
                if tables[role].checksum != metadata["sha256"]:
                    raise DbfReadError("Šaltinio hash neatitinka skaitymo rezultato.")
            estimates, lines, warnings = reconstruct(tables)
    except DbfReadError as exc:
        raise ServiceError(422, str(exc)) from exc
    imported = HistoricalImport(
        source_hash=checksum,
        source_reference=", ".join(v["name"] for v in roles.values()),
        source_files=list(roles.values()),
        encoding=encoding,
        parser_version=VERSION,
        warnings=warnings,
    )
    try:
        session.add(imported)
        session.flush()
        index = {}
        for key, values in estimates:
            estimate = HistoricalEstimate(historical_import_id=imported.id, **values)
            session.add(estimate)
            session.flush()
            index[key] = estimate.id
        for values in lines:
            values = dict(values)
            estimate_id = index[values.pop("estimate_key")]
            session.add(HistoricalLine(historical_estimate_id=estimate_id, **values))
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(
            select(HistoricalImport).where(HistoricalImport.source_hash == checksum)
        )
        if existing and existing.encoding == encoding:
            return import_summary(session, existing) | {"duplicate": True}
        raise ServiceError(409, "Importo konfliktas. Atnaujinkite istoriją.") from exc
    logger.info(
        "history_import id=%s estimates=%d lines=%d warnings=%d",
        imported.id,
        len(estimates),
        len(lines),
        len(warnings),
    )
    return import_summary(session, imported) | {"duplicate": False}


def import_summary(session, imported):
    estimates = session.scalars(
        select(HistoricalEstimate).where(HistoricalEstimate.historical_import_id == imported.id)
    ).all()
    lines = session.scalars(
        select(HistoricalLine)
        .join(HistoricalEstimate)
        .where(HistoricalEstimate.historical_import_id == imported.id)
    ).all()
    return {
        "id": imported.id,
        "source_hash": imported.source_hash,
        "source_reference": imported.source_reference,
        "source_files": imported.source_files,
        "encoding": imported.encoding,
        "imported_at": imported.imported_at,
        "import_status": imported.import_status,
        "parser_version": imported.parser_version,
        "warning_count": len(imported.warnings),
        "warnings": imported.warnings,
        "estimates": [
            {
                "id": e.id,
                "name": e.name,
                "project_name": e.project_name,
                "system_type": e.system_type,
                "system_evidence": e.system_evidence,
                "source_date": e.source_date,
            }
            for e in estimates
        ],
        "line_count": len(lines),
        "work_count": sum(item_line.line_type == "Work" for item_line in lines),
        "confirmed_count": sum(item_line.status == "CONFIRMED" for item_line in lines),
        "rejected_count": sum(item_line.status == "REJECTED" for item_line in lines),
    }


def line_view(line, estimate):
    return {
        key: str(value) if isinstance(value := getattr(line, key), Decimal) else value
        for key in [
            "id",
            "historical_estimate_id",
            "line_type",
            "description",
            "sistela_code",
            "sistela_original_description",
            "unit",
            "quantity",
            "historical_price",
            "section_name",
            "system_type",
            "evidence_type",
            "confidence",
            "status",
            "version",
            "reviewed_at",
        ]
    } | {
        "estimate_name": estimate.name,
        "project_name": estimate.project_name,
        "source_date": estimate.source_date,
        "system_evidence": estimate.system_evidence,
        "bulk_eligible": line.evidence_type != "AMBIGUOUS"
        and line.line_type == "Work"
        and line.confidence >= Decimal("0.85")
        and bool(line.unit and line.system_type and line.sistela_code and line.description),
    }


def historical_lines(
    session, import_id=None, search="", system="", code="", status="", limit=200, offset=0
):
    query = select(HistoricalLine, HistoricalEstimate).join(HistoricalEstimate)
    if import_id:
        query = query.where(HistoricalEstimate.historical_import_id == import_id)
    if system:
        query = query.where(HistoricalLine.system_type == system)
    if code:
        query = query.where(HistoricalLine.sistela_code.contains(code, autoescape=True))
    if status:
        query = query.where(HistoricalLine.status == status)
    if search:
        query = query.where(
            HistoricalLine.normalized_description.contains(normalize_text(search), autoescape=True)
        )
    from sqlalchemy import func

    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.execute(
        query.order_by(HistoricalEstimate.id, HistoricalLine.id).offset(offset).limit(limit)
    ).all()
    return {"total": total, "items": [line_view(line, estimate) for line, estimate in rows]}


def historical_evidence(session, line_id):
    line = session.get(HistoricalLine, line_id)
    if not line:
        raise ServiceError(404, "Istorinė eilutė nerasta.")
    estimate = session.get(HistoricalEstimate, line.historical_estimate_id)
    imported = session.get(HistoricalImport, estimate.historical_import_id)
    reviews = session.scalars(
        select(HistoricalReview)
        .where(HistoricalReview.historical_line_id == line.id)
        .order_by(HistoricalReview.created_at)
    ).all()
    return line_view(line, estimate) | {
        "evidence": line.evidence,
        "external_key": line.external_key,
        "estimate_source": estimate.source_reference,
        "imported_at": imported.imported_at,
        "source_files": imported.source_files,
        "reviews": [
            {
                "status": r.status,
                "previous_status": r.previous_status,
                "system_type": r.system_type,
                "created_at": r.created_at,
                "acknowledged_ambiguity": r.acknowledged_ambiguity,
            }
            for r in reviews
        ],
    }


def review_candidates(session, request: HistoricalReviewRequest):
    if len({i.id for i in request.items}) != len(request.items):
        raise ServiceError(422, "Pasikartojantis kandidatas.")
    try:
        for item in request.items:
            line = session.get(HistoricalLine, item.id)
            if not line or line.status == "NOT_APPLICABLE":
                raise ServiceError(422, "Kandidatas nerastas arba tai medžiaga.")
            if line.version != item.version:
                raise ServiceError(409, "Kandidatas jau pakeistas. Atnaujinkite istoriją.")
            system = item.system_type or line.system_type
            if request.status == "CONFIRMED":
                if not system or not line.unit or not line.description or not line.sistela_code:
                    raise ServiceError(
                        422, "Patvirtinimui būtina sistema, vienetas, aprašymas ir kodas."
                    )
                if line.evidence_type == "AMBIGUOUS" and (
                    len(request.items) > 1 or not request.acknowledge_ambiguity
                ):
                    raise ServiceError(
                        422,
                        "Neaiškų kandidatą peržiūrėkite atskirai ir aiškiai patvirtinkite įrodymų patikrą.",
                    )
                if len(request.items) > 1 and (
                    line.line_type != "Work" or line.confidence < Decimal("0.85")
                ):
                    raise ServiceError(
                        422, "Masinis patvirtinimas skirtas tik patikrintoms darbų eilutėms."
                    )
            if line.status == request.status and system == line.system_type:
                continue
            previous = line.status
            result = session.execute(
                update(HistoricalLine)
                .where(HistoricalLine.id == line.id, HistoricalLine.version == item.version)
                .values(
                    status=request.status,
                    system_type=system,
                    version=item.version + 1,
                    reviewed_at=utc_now(),
                )
            )
            if result.rowcount != 1:
                raise ServiceError(409, "Kandidatas jau pakeistas.")
            session.add(
                HistoricalReview(
                    historical_line_id=line.id,
                    previous_status=previous,
                    status=request.status,
                    system_type=system,
                    acknowledged_ambiguity=request.acknowledge_ambiguity,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"updated": len(request.items)}


def historical_suggestions(session, current):
    if current.line_type != "Work":
        return []
    rows = session.execute(
        select(HistoricalLine, HistoricalEstimate)
        .join(HistoricalEstimate)
        .where(
            HistoricalLine.status.in_(["CANDIDATE", "CONFIRMED"]),
            HistoricalLine.system_type == current.system_type,
            HistoricalLine.line_type.in_(["Work", "Other"]),
        )
    ).all()
    normalized = normalize_text(current.project_description)
    groups = defaultdict(list)
    for line, estimate in rows:
        similarity = ratio(normalized, line.normalized_description) / 100
        compatibility = unit_compatibility(current.unit, line.unit)
        # Confirmation validates historical evidence, not the current description.
        # Reuse it as a same-system/unit shortlist even when wording differs;
        # retain the low text score and require explicit current-row approval.
        confirmed = line.status == "CONFIRMED"
        if confirmed and compatibility["status"] not in {"IDENTICAL", "CONVERTIBLE"}:
            continue
        if (similarity < 0.45 and not confirmed) or not line.sistela_code:
            continue
        groups[(line.sistela_code, line.unit)].append((line, estimate, similarity))
    result = []
    for (code, unit), members in groups.items():

        def rank(member):
            line, _, similarity = member
            exact = line.description == current.project_description
            strong = line.evidence_type != "AMBIGUOUS"
            tier = (
                2
                if line.status == "CONFIRMED"
                else 3
                if strong and exact
                else 4
                if strong
                else 5
            )
            return tier, -similarity, -(line.status == "CONFIRMED")

        members.sort(key=rank)
        best, _, similarity = members[0]
        compatibility = unit_compatibility(current.unit, unit)
        compatible = compatibility["status"] == "IDENTICAL" and (
            best.evidence_type != "AMBIGUOUS" or best.status == "CONFIRMED"
        )
        score = min(Decimal("0.94"), Decimal(str(similarity)) * best.confidence)
        if not compatible:
            score = min(score, Decimal("0.49"))
        # A repeated identical position in another snapshot isn't another historical use.
        distinct = {
            json.dumps(
                [line.external_key, line.description, line.sistela_code, line.unit], sort_keys=True
            )
            for line, _, _ in members
        }
        projects = {
            json.dumps({k: e.external_key.get(k, e.id) for k in ("KOMPLEKSAS", "OBJEKTAS")}, sort_keys=True)
            for _, e, _ in members
        }
        dates = [e.source_date for _, e, _ in members if e.source_date]
        result.append(
            {
                "mapping_id": "history:" + best.id,
                "sistela_code": code,
                "sistela_description": "",
                "source_unit": unit,
                "confidence": str(score.quantize(Decimal(".01"))),
                "method": "exact"
                if best.description == current.project_description
                else "normalized"
                if best.normalized_description == normalized
                else "fuzzy",
                "confirmed_count": sum(
                    item_line.status == "CONFIRMED" for item_line, _, _ in members
                ),
                "compatible": compatible,
                "evidence_eligible": best.evidence_type != "AMBIGUOUS" or best.status == "CONFIRMED",
                "last_used_at": None,
                "source_date": max(dates) if dates else None,
                "last_used_kind": "estimate KODAT; not a proven usage date",
                "origin": "historical",
                "historical_confirmed": best.status == "CONFIRMED",
                "priority": rank(members[0])[0],
                "usage_count": len(distinct),
                "project_count": len(projects),
                "estimate_count": len({e.id for _, e, _ in members}),
                "matching_descriptions": sorted(
                    {item_line.description for item_line, _, _ in members}
                ),
                "evidence_quality": sorted(
                    {item_line.evidence_type for item_line, _, _ in members}
                ),
                "evidence_ids": [item_line.id for item_line, _, _ in members],
                "unit_compatibility": compatibility,
            }
        )
    return result
