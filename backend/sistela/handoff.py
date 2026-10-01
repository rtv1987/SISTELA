"""Pure review invariants shared by every mutation and handoff consumer."""

from decimal import Decimal

from .parsers.common import normalize_unit
from .units import convert_quantity, unit_compatibility


def target(line):
    conversion = (line.review_data or {}).get("conversion")
    if not conversion:
        return line.quantity, line.unit, True
    try:
        valid = (
            conversion["confirmed_by_user"] is True
            and Decimal(conversion["source_quantity"]) == line.quantity
            and normalize_unit(conversion["source_unit"]) == normalize_unit(line.unit)
            and unit_compatibility(line.unit, conversion["target_unit"])["status"] == "CONVERTIBLE"
            and Decimal(conversion["target_quantity"])
            == convert_quantity(line.quantity, line.unit, conversion["target_unit"])
        )
        return Decimal(conversion["target_quantity"]), conversion["target_unit"], valid
    except (KeyError, ValueError, ArithmeticError):
        return line.quantity, line.unit, False


def invalidate_review(line, values):
    review = dict(line.review_data or {})
    source_changed = any(
        k in values and values[k] != getattr(line, k) for k in ("quantity", "unit")
    )
    semantic = any(
        k in values and values[k] != getattr(line, k)
        for k in (
            "project_description",
            "system_type",
            "line_type",
            "sistela_code",
            "sistela_original_description",
        )
    )
    if source_changed and review.get("conversion"):
        review["conversion"] = {**review["conversion"], "confirmed_by_user": False}
        values["mapping_status"] = "needs_review"
    if semantic:
        review.pop("suggestion", None)
        review.pop("manual", None)
    if values.get('line_type',line.line_type) != line.line_type:
        review.pop('export_options',None)
        review.pop('ngr_evidence',None)
    if review.get('generated_code') and not review.get('conversion') and 'unit' in values:
        review['normative_unit'] = values['unit']
    if any(
        k in values and values[k] != getattr(line, k)
        for k in ("material_price", "work_price", "line_type")
    ):
        field = (
            "material_price"
            if values.get("line_type", line.line_type) in {"Material","Equipment"}
            else "work_price"
        )
        review["price_status"] = (
            "ENTERED" if values.get(field, getattr(line, field)) is not None else "MISSING"
        )
    if source_changed or semantic:
        review.pop("duplicates", None)
    values["review_data"] = review
