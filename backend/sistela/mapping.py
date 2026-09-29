"""Deterministic suggestions derived exclusively from explicit local confirmations."""
from decimal import Decimal

from pydantic import Field
from rapidfuzz.fuzz import ratio
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from .grid import owned_line, update_versioned
from .handoff import target
from .history import historical_suggestions
from .models import MappingConfirmation, SistelaMapping, utc_now
from .parsers.common import normalize_text, normalize_unit
from .schemas import InputModel
from .services import ServiceError
from .units import unit_compatibility


class ConfirmMapping(InputModel):
    version: int = Field(ge=1)
    sistela_code: str = Field(min_length=1, max_length=100)
    sistela_original_description: str = Field(default="", max_length=4000)
    normative_unit: str = Field(min_length=1, max_length=40)


class ApplyMapping(InputModel):
    version: int = Field(ge=1)
    mapping_id: str


class EntryUpdate(InputModel):
    version: int = Field(ge=1)
    entered: bool


def suggestions(session, line):
    if line.line_type != "Work":
        return []
    normalized = normalize_text(line.project_description)
    mappings = session.scalars(select(SistelaMapping).where(SistelaMapping.system_type == line.system_type,
        SistelaMapping.confirmed_count > 0)).all()
    latest = {}
    for item in mappings:
        key = (item.normalized_source_text, item.source_unit)
        if key not in latest or (item.last_used_at or "") > (latest[key].last_used_at or ""):
            latest[key] = item
    result = []
    for item in mappings:
        similarity = ratio(normalized, item.normalized_source_text) / 100
        if similarity < .45:
            continue
        method = "exact" if item.source_text == line.project_description else "normalized" if normalized == item.normalized_source_text else "fuzzy"
        compatibility = unit_compatibility(line.unit, item.source_unit)
        compatible = compatibility["status"] == "IDENTICAL"
        score = .94 if method == "exact" else .90 if method == "normalized" else similarity * .86
        newest = latest[(item.normalized_source_text, item.source_unit)].id == item.id
        score += .05 if newest else min(item.confirmed_count, 4) * .001
        if not compatible:
            score = min(score, .49)
        result.append({"mapping_id": item.id, "sistela_code": item.sistela_code,
            "sistela_description": item.sistela_description, "source_unit": item.source_unit,
            "confidence": str(Decimal(str(min(score, .99))).quantize(Decimal('.01'))),
            "method": method, "confirmed_count": item.confirmed_count, "compatible": compatible,
            "last_used_at": item.last_used_at, "origin": "user", "unit_compatibility": compatibility,
            "priority": 0 if method == "exact" else 1 if method == "normalized" else 6})
    result.extend(historical_suggestions(session, line))
    # Preserve correction recency within each tier; explicit exact confirmations rank first.
    result.sort(key=lambda x: (Decimal(x["confidence"]), x["last_used_at"] or "", x["confirmed_count"]), reverse=True)
    result.sort(key=lambda x: (not x["compatible"], x["priority"]))
    review = line.review_data or {}
    _, unit, valid = target(line)
    for candidate in result:
        candidate["compatible"] = (valid and normalize_unit(unit) == normalize_unit(candidate["source_unit"])
            and candidate.get("evidence_eligible", True))
    result.sort(key=lambda x: (not x["compatible"], x["priority"]))
    return [r for r in result if r["mapping_id"] not in review.get("rejected_ids", [])][:5]


def apply_suggestion(session, project_id, line_id, request: ApplyMapping):
    line = owned_line(session, project_id, line_id)
    candidate = next((s for s in suggestions(session, line) if s["mapping_id"] == request.mapping_id), None)
    if not candidate or not candidate["compatible"]:
        raise ServiceError(422, "Pasiūlymas nebetinka arba nesutampa normatyvinis vienetas.")
    update_versioned(session, line, request.version, {
        "sistela_code": candidate["sistela_code"], "sistela_original_description": candidate["sistela_description"],
        "confidence": Decimal(candidate["confidence"]), "mapping_status": "suggested", "entered_at": None,
        "review_data": {**(line.review_data or {}), "suggestion": candidate, "suggestion_offered": True, "manual": False}})
    session.commit()
    session.refresh(line)
    return line


def confirm_mapping(session, project_id, line_id, request: ConfirmMapping):
    line = owned_line(session, project_id, line_id)
    if line.version != request.version:
        raise ServiceError(409, "Eilutė jau pakeista. Atnaujinkite duomenis.")
    if line.line_type != "Work":
        raise ServiceError(422, "Normatyvų istorija skirta darbų eilutėms.")
    unit = normalize_unit(request.normative_unit)
    if not target(line)[2] or unit != normalize_unit(target(line)[1]):
        raise ServiceError(422, "Nesutampa vienetai. Peržiūroje aiškiai patvirtinkite konversiją.")
    if line.mapping_status == "confirmed" and line.sistela_code == request.sistela_code and line.sistela_original_description == request.sistela_original_description:
        return line
    previous = line.sistela_code
    review = dict(line.review_data or {})
    review.setdefault("suggestion_offered", bool(suggestions(session, line)))
    candidate = review.get("suggestion", {})
    review["confirmation_kind"] = "unchanged" if candidate.get("sistela_code") == request.sistela_code else "changed" if candidate else "manual"
    review["normative_unit"] = unit
    review["manual"] = bool(review.get("manual")) or not candidate
    if candidate and candidate.get("sistela_code") != request.sistela_code:
        review.pop("suggestion", None)
    try:
        update_versioned(session, line, request.version, {"sistela_code": request.sistela_code,
            "sistela_original_description": request.sistela_original_description, "mapping_status": "confirmed", "entered_at": None,
            "confidence": line.confidence if previous == request.sistela_code else None, "review_data": review})
        normalized = normalize_text(line.project_description)
        item = session.scalar(select(SistelaMapping).where(SistelaMapping.system_type == line.system_type,
            SistelaMapping.normalized_source_text == normalized, SistelaMapping.source_unit == unit,
            SistelaMapping.sistela_code == request.sistela_code))
        if not item:
            item = SistelaMapping(system_type=line.system_type, source_text=line.project_description,
                normalized_source_text=normalized, source_unit=unit, sistela_code=request.sistela_code,
                sistela_description=request.sistela_original_description)
            session.add(item)
            session.flush()
        session.execute(update(SistelaMapping).where(SistelaMapping.id == item.id).values(
            source_text=line.project_description, sistela_description=request.sistela_original_description,
            confirmed_count=SistelaMapping.confirmed_count + 1, usage_count=SistelaMapping.usage_count + 1,
            last_used_at=utc_now(), updated_at=utc_now()))
        session.add(MappingConfirmation(mapping_id=item.id, project_id=project_id, line_id=line.id,
            previous_code=previous, selected_code=request.sistela_code, source_text=line.project_description))
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ServiceError(409, "Istorija pakeista kitoje užklausoje. Pakartokite patvirtinimą.") from exc
    session.refresh(line)
    return line


def mark_entry(session, project_id, line_id, request: EntryUpdate):
    line = owned_line(session, project_id, line_id)
    if request.entered and (not target(line)[2] or line.quantity <= 0 or not line.unit or (line.line_type == "Work" and
            (line.mapping_status != "confirmed" or not line.sistela_code))):
        raise ServiceError(422, "Prieš suvedimą patikrinkite vienetą ir patvirtinkite darbo normatyvą.")
    from .workflow import validate_project_for_sistela
    if request.entered:
        row = next(r for r in validate_project_for_sistela(session, project_id)["rows"] if r["id"] == line_id)
        if any(i["severity"] == "BLOCKING" for i in row["issues"]):
            raise ServiceError(422, "Eilutėje liko blokuojančių peržiūros klausimų.")
    update_versioned(session, line, request.version, {"entered_at": utc_now() if request.entered else None})
    from .services import get_project
    get_project(session, project_id).status = validate_project_for_sistela(session, project_id)["status"]
    session.commit()
    session.refresh(line)
    return line
