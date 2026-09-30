"""Project-export preparation, with explicit blockers instead of speculative DBFs."""
from decimal import Decimal
from hashlib import sha256

from sqlalchemy import select

from .dbf_export import DbfExportBlocked, encode_field
from .export_model import normalized_estimate
from .grid import active_lines
from .models import EstimateSection, HistoricalEstimate
from .parsers.dbf import DbfField
from .services import get_project
from .workflow import validate_project_for_sistela

PROJECT_BLOCKERS = [
    "REAL_SISTELA_ACCEPTANCE_PENDING: TEST_A and TEST_B must be accepted by Darius.",
    "CALCULATED_FIELDS_UNKNOWN: dd resources, pd quantities/prices and td/od totals cannot be synthesized.",
    "IDENTIFIER_IMPORT_BEHAVIOR_UNKNOWN: global collisions/remapping cannot be established from one archive.",
    "NEW_ARCHIVE_NAMING_AND_REQUIRED_FIELDS_UNKNOWN: no new-project profile proven.",
    "UNIT_CATALOGUE_INCOMPLETE: MATOVNT codes for arbitrary target units are unproven.",
]


def allocate_identifiers(project_id, section_rows, reserved_complexes=()):
    """Deterministic proposal, not an accepted SISTELA identifier protocol."""
    complex_id = "A" + sha256(project_id.encode("utf-8")).hexdigest()[:9].upper()
    if complex_id in reserved_complexes:
        raise DbfExportBlocked("COMPLEX_ID_COLLISION: choose an independently reserved namespace")
    if len(section_rows) > 9999:
        raise DbfExportBlocked("SECTION_ID_WIDTH_EXCEEDED")
    rows = []
    for section, (section_id, row_ids) in enumerate(section_rows, 1):
        if len(row_ids) > 9999:
            raise DbfExportBlocked("LINE_ID_WIDTH_EXCEEDED")
        for ordinal, row_id in enumerate(row_ids, 1):
            rows.append({"source_line_id": row_id, "source_section_id": section_id,
                         "KOMPLEKSAS": complex_id, "OBJEKTAS": 1, "RANGOVAS": 1, "SAMATA": 1,
                         "SKYRIUS": section, "SUSDARB1": 0,
                         "SAM_EILUTE": ordinal, "DET_EILUTE": ordinal})
    if len({r["source_line_id"] for r in rows}) != len(rows):
        raise DbfExportBlocked("DUPLICATE_SOURCE_LINE_ID")
    return rows


def project_export_plan(session, project_id):
    project = get_project(session, project_id)
    model = normalized_estimate(session, project_id)
    normalized_rows = {r["id"]: r for section in model["sections"] for r in section["rows"]}
    normalized_sections = {section['id']:section for section in model['sections']}
    lines = active_lines(session, project_id)
    report = validate_project_for_sistela(session, project_id)
    blockers = list(PROJECT_BLOCKERS)
    sections = {s.id: s for s in session.scalars(select(EstimateSection).where(
        EstimateSection.project_id == project_id).order_by(EstimateSection.sort_order, EstimateSection.id))}
    grouped = {}
    rows = []

    def fits(field, value, source):
        try:
            encode_field(field, value)
        except DbfExportBlocked:
            blockers.append(f"{source}: {field.name} does not fit cp1257/width/scale")

    fits(DbfField("PAVADIN", "C", 180, 0), project.name, "project")
    if not project.name.strip() or not lines:
        blockers.append("PROJECT_HIERARCHY_EMPTY")
    for item in report["rows"]:
        for issue in item["issues"]:
            if issue["severity"] == "BLOCKING":
                blockers.append(f"{item['id']}: {issue['category']}")
    for line in lines:
        normalized = normalized_rows[line.id]
        quantity, unit, valid = (normalized["target_quantity"], normalized["target_unit"], normalized["conversion_valid"])
        section_id = line.section_id or ("manual-" + line.line_type)
        section_name = normalized_sections[section_id]['name']
        if not section_name or (line.section_id and line.section_id not in sections):
            blockers.append(f"{line.id}: SECTION_MISSING")
        grouped.setdefault(section_id, []).append(line.id)
        for field, value in ((DbfField("KIEKIS", "N", 13, 6), Decimal(quantity)),
                             (DbfField("IKAINIS", "C", 18, 0), normalized['selected_code']),
                             (DbfField("PAVADIN", "C", 240, 0), normalized['output_description']),
                             (DbfField("MATO_PAV", "C", 20, 0), unit),
                             (DbfField("SECTION_NAME", "C", 180, 0), section_name)):
            fits(field, value, line.id)
        for price in (line.material_price, line.work_price):
            fits(DbfField("KAINA", "N", 12, 4), price, line.id)
        rows.append({"source_line_id": line.id, "source_section_id": section_id,
                     "section_name": section_name, "line_type": line.line_type,
                     "project_description": normalized['source_description'], "sistela_code": normalized['selected_code'],
                     "output_description": normalized['output_description'],
                     "source_quantity": normalized['source_quantity'], "source_unit": normalized['source_unit'],
                     "target_quantity": str(quantity), "target_unit": unit,
                     "conversion_valid": valid, "mapping_status": line.mapping_status,
                     "material_price": normalized['material_price'],
                     "work_price": normalized['work_price']})
    try:
        reserved = [estimate.external_key.get("KOMPLEKSAS") for estimate in session.scalars(select(HistoricalEstimate))]
        identifiers = allocate_identifiers(project_id, list(grouped.items()), reserved)
    except DbfExportBlocked as exc:
        blockers.extend(exc.errors)
        identifiers = []
    return {"mode": "PROJECT_EXPORT", "status": "BLOCKED", "production": False,
            "normalized_estimate": model, "project_id": project.id, "project_name": project.name, "estimate_name": project.name,
            "blockers": blockers, "rows": rows, "proposed_identifiers": identifiers,
            "warnings": ["Plan only: no financial values or normative resources generated."]}
