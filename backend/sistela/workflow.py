"""Local estimator review. Validation never implies verified SISTELA import."""

import hashlib
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import Field
from rapidfuzz.fuzz import ratio
from sqlalchemy import select
from sqlalchemy.orm import Session

from .grid import active_lines, owned_line, update_versioned
from .handoff import target
from .models import SourceDocument, utc_now
from .parsers.common import normalize_text, normalize_unit
from .schemas import InputModel, LineOut
from .services import ServiceError, get_project
from .units import convert_quantity, unit_compatibility

KNOWN_UNITS = {"m", "100m", "vnt.", "kompl.", "m2", "m3", "kg", "t", "val.", "l", "km"}


def duplicate_key(a, b):
    return hashlib.sha256(
        repr(
            sorted(
                (r.id, r.project_description, r.unit, r.section_id, r.system_type) for r in (a, b)
            )
        ).encode()
    ).hexdigest()


def validate_project_for_sistela(session, project_id):
    from .mapping import suggestions

    project = get_project(session, project_id)
    lines = active_lines(session, project_id)
    documents = {
        d.id: d.filename
        for d in session.scalars(
            select(SourceDocument).where(SourceDocument.project_id == project_id)
        )
    }
    rows = []
    for line in lines:
        review = line.review_data or {}
        issues = []

        def issue(category, severity, message):
            issues.append(dict(category=category, severity=severity, message=message))

        quantity, unit, valid = target(line)
        if line.quantity <= 0:
            issue("MISSING_QUANTITY", "BLOCKING", "Kiekis turi būti teigiamas.")
        if normalize_unit(line.unit) not in KNOWN_UNITS:
            issue("UNKNOWN_UNIT", "BLOCKING", "Nežinomas vienetas. Patikrinkite lentelėje.")
        if not valid:
            issue(
                "UNIT_MISMATCH",
                "BLOCKING",
                "Konversija nepatvirtinta arba pasikeitė pradinis kiekis / vienetas.",
            )
        if (
            line.line_type == "Other"
            or not line.project_description.strip()
            or not line.output_description.strip()
        ):
            issue("INVALID_ROW_STATE", "BLOCKING", "Patikrinkite eilutės tipą ir pavadinimą.")
        candidates = suggestions(session, line) if line.line_type == "Work" else []
        evidence = review.get("suggestion", {})
        if line.line_type == "Work":
            if not line.sistela_code.strip():
                issue("MISSING_SISTELA_CODE", "BLOCKING", "Pasirinkite SISTELA darbų kodą.")
            if line.mapping_status != "confirmed":
                issue(
                    "UNCONFIRMED_HISTORICAL_MAPPING"
                    if evidence.get("origin") == "historical"
                    else "UNCONFIRMED_MAPPING",
                    "BLOCKING",
                    "Reikalingas vartotojo patvirtinimas.",
                )
            if evidence.get("source_unit") and normalize_unit(
                evidence["source_unit"]
            ) != normalize_unit(unit):
                issue(
                    "UNIT_MISMATCH",
                    "BLOCKING",
                    "Pasirinkto pasiūlymo ir tikslinis vienetai nesutampa.",
                )
            if (
                candidates
                and not candidates[0]["compatible"]
                and line.mapping_status != "confirmed"
            ):
                issue(
                    "UNIT_MISMATCH",
                    "BLOCKING",
                    "Pasiūlymo vienetą reikia patikrinti ir aiškiai patvirtinti konversiją.",
                )
            if line.confidence is not None and line.confidence < Decimal("0.7"):
                issue(
                    "LOW_CONFIDENCE_MAPPING",
                    "WARNING",
                    "Silpnas teksto atitikimas; patikrinkite įrodymus.",
                )
            if evidence.get("origin") == "historical":
                issue(
                    "HISTORICAL_ONLY",
                    "WARNING",
                    "Istorinis tekstas nėra patvirtintas katalogo originalas.",
                )
            descriptions = evidence.get("matching_descriptions") or []
            if (
                descriptions
                and max(
                    ratio(normalize_text(line.output_description), normalize_text(d))
                    for d in descriptions
                )
                < 50
            ):
                issue(
                    "DESCRIPTION_DIFFERENCE",
                    "WARNING",
                    "Galutinis tekstas labai skiriasi nuo istorinių aprašymų.",
                )
        price = line.material_price if line.line_type == "Material" else line.work_price
        price_status = review.get("price_status", "ENTERED" if price is not None else "MISSING")
        if price is None:
            issue("PRICE_MISSING", "WARNING", "Kaina nenurodyta.")
        if price_status == "HISTORICAL_REFERENCE":
            issue(
                "HISTORICAL_PRICE",
                "WARNING",
                "Kaina tik istorinė nuoroda, ne dabartinis kainos patvirtinimas.",
            )
        duplicates = []
        for other in lines:
            if (
                other.id != line.id
                and other.line_type == line.line_type
                and other.section_id == line.section_id
                and other.system_type == line.system_type
                and normalize_unit(other.unit) == normalize_unit(line.unit)
                and ratio(
                    normalize_text(other.project_description),
                    normalize_text(line.project_description),
                )
                >= 95
            ):
                key = duplicate_key(line, other)
                if key not in review.get("duplicates", []) and key not in (
                    other.review_data or {}
                ).get("duplicates", []):
                    duplicates.append({"id": other.id, "key": key})
        if duplicates:
            issue(
                "POSSIBLE_DUPLICATE",
                "WARNING",
                "Galimas dublikatas. Palikite abu arba sujunkite rankiniu būdu lentelėje.",
            )
        rows.append(
            dict(
                id=line.id,
                issues=issues,
                category=issues[0]["category"] if issues else "READY",
                target_quantity=format(quantity, "f"),
                target_unit=unit,
                conversion_valid=valid,
                price_status=price_status,
                duplicates=duplicates,
                suggestions=candidates,
                source_filename=documents.get(line.source_document_id),
                manual=bool(review.get("manual")),
            )
        )
    rows.sort(
        key=lambda r: (
            not any(i["severity"] == "BLOCKING" for i in r["issues"]),
            not bool(r["issues"]),
        )
    )
    blocking = sum(i["severity"] == "BLOCKING" for r in rows for i in r["issues"])
    warnings = sum(i["severity"] == "WARNING" for r in rows for i in r["issues"])
    works = [r for r in lines if r.line_type == "Work"]
    if not lines:
        blocking += 1
    confirmed = sum(r.mapping_status == "confirmed" for r in works)
    status = (
        ("HANDED_OFF" if works and all(r.entered_at for r in works) else "READY_FOR_SISTELA")
        if not blocking
        else ("MAPPING_IN_PROGRESS" if any(r.sistela_code for r in works) else "NEEDS_REVIEW")
    )
    statistics = dict(
        imported_line_count=sum(bool(r.source_document_id) for r in lines),
        auto_suggested_mapping_count=sum(
            (line.review_data or {}).get(
                "suggestion_offered",
                bool(next(r for r in rows if r["id"] == line.id)["suggestions"]),
            )
            for line in works
        ),
        confirmed_without_change_count=sum(
            r.mapping_status == "confirmed"
            and (r.review_data or {}).get("confirmation_kind") == "unchanged"
            for r in works
        ),
        changed_mapping_count=sum(
            r.mapping_status == "confirmed"
            and (r.review_data or {}).get("confirmation_kind") == "changed"
            for r in works
        ),
        manual_mapping_count=sum(bool((r.review_data or {}).get("manual")) for r in works),
        review_issue_count=blocking + warnings,
        entry_mode_completed_count=sum(bool(r.entered_at) for r in works),
    )
    return dict(
        project_id=project.id,
        status=status,
        blocking=blocking,
        warnings=warnings,
        rows=rows,
        statistics=statistics,
        summary=dict(
            total=len(lines),
            materials=sum(r.line_type == "Material" for r in lines),
            works=len(works),
            mapped=sum(bool(r.sistela_code) for r in works),
            confirmed=confirmed,
            unresolved=len(works) - confirmed,
            needs_review=sum(bool(r["issues"]) for r in rows),
            entered=statistics["entry_mode_completed_count"],
            missing_prices=sum(
                (r.material_price if r.line_type == "Material" else r.work_price) is None
                for r in lines
            ),
            confirmed_prices=sum(r["price_status"] == "CONFIRMED" for r in rows),
            conversions=sum(
                bool((r.review_data or {}).get("conversion")) and target(r)[2] for r in lines
            ),
        ),
    )


class ReviewAction(InputModel):
    version: int = Field(ge=1)
    action: Literal["convert", "cancel_conversion", "reject", "manual", "keep_both", "price"]
    target_unit: str = Field(default="", max_length=40)
    duplicate_id: str = ""
    mapping_id: str = Field(default="", max_length=300)
    price_status: Literal["MISSING", "ENTERED", "HISTORICAL_REFERENCE", "CONFIRMED"] = "MISSING"


def review_line(session, project_id, line_id, request):
    line = owned_line(session, project_id, line_id)
    review = dict(line.review_data or {})
    from .mapping import suggestions

    review.setdefault("suggestion_offered", bool(suggestions(session, line)))
    values = {"entered_at": None}
    if (
        request.action in {"convert", "cancel_conversion", "reject", "manual"}
        and line.line_type != "Work"
    ):
        raise ServiceError(422, "Šis veiksmas skirtas tik darbams.")
    if request.action == "convert":
        rule = unit_compatibility(line.unit, request.target_unit)
        if rule["status"] != "CONVERTIBLE" or line.quantity <= 0:
            raise ServiceError(422, "Leidžiama tik aiški m ↔ 100M konversija su teigiamu kiekiu.")
        review["conversion"] = dict(
            source_quantity=str(line.quantity),
            source_unit=line.unit,
            target_quantity=format(
                convert_quantity(line.quantity, line.unit, request.target_unit), "f"
            ),
            target_unit=rule["target"],
            conversion_rule=f"{rule['source']} -> {rule['target']} x {rule['factor']}",
            confirmed_by_user=True,
            confirmed_at=utc_now(),
        )
        values["mapping_status"] = "needs_review"
    elif request.action == "cancel_conversion":
        review.pop("conversion", None)
        review.pop("suggestion", None)
        values["mapping_status"] = "needs_review"
    elif request.action == "reject":
        selected = request.mapping_id or review.get("suggestion", {}).get("mapping_id", "")
        if request.mapping_id:
            if selected not in [s["mapping_id"] for s in suggestions(session, line)]:
                raise ServiceError(422, "Pasiūlymas neberastas.")
        review["rejected_ids"] = list(set(review.get("rejected_ids", []) + [selected]))
        review.pop("confirmation_kind", None)
        review.pop("suggestion", None)
        values.update(mapping_status="rejected", sistela_code="", confidence=None)
    elif request.action == "manual":
        review["manual"] = True
        values["mapping_status"] = "needs_review"
    elif request.action == "keep_both":
        other = owned_line(session, project_id, request.duplicate_id)
        review["duplicates"] = list(
            set(review.get("duplicates", []) + [duplicate_key(line, other)])
        )
    elif request.action == "price":
        price = line.material_price if line.line_type == "Material" else line.work_price
        if request.price_status in {"ENTERED", "CONFIRMED"} and price is None:
            raise ServiceError(422, "Pirma įveskite kainą lentelėje.")
        if request.price_status == "MISSING" and price is not None:
            raise ServiceError(422, "Kaina jau įvesta.")
        review["price_status"] = request.price_status
    values["review_data"] = review
    update_versioned(session, line, request.version, values)
    session.commit()
    return line


def workflow_router(session_dependency):
    router = APIRouter()

    @router.get("/projects/{project_id}/validation")
    def validation(project_id: str, session: Session = Depends(session_dependency)):
        return validate_project_for_sistela(session, project_id)

    @router.post("/projects/{project_id}/validate")
    def validate(project_id: str, session: Session = Depends(session_dependency)):
        report = validate_project_for_sistela(session, project_id)
        get_project(session, project_id).status = report["status"]
        session.commit()
        return report

    @router.post("/projects/{project_id}/lines/{line_id}/review", response_model=LineOut)
    def review(
        project_id: str,
        line_id: str,
        request: ReviewAction,
        session: Session = Depends(session_dependency),
    ):
        return review_line(session, project_id, line_id, request)

    return router
