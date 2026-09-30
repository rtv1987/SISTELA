"""Compatibility adapter from normalized schedules to application estimate lines."""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .common import clean_text
from .schedule import NormalizedSchedule

PARSER_VERSION = "pdf-structure-2.0"


class PdfImportError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass
class ParsedLine:
    source_position: str
    project_description: str
    technical_reference: str
    unit: str
    quantity: Decimal
    notes: str
    line_type: str
    source_page: int
    source_raw_text: str


@dataclass
class PdfResult:
    page_count: int
    extracted_text: str
    lines: list[ParsedLine] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    diagnostics: list[dict] = field(default_factory=list)
    needs_selection: bool = False
    schedule: NormalizedSchedule | None = None


def parse_table(rows, page, initial_type=None):
    """Compatibility entry point; uses the same semantic engine as PDF imports."""
    from .schedule import Cell, TableCandidate, header_roles, infer_columns, normalize

    candidate = TableCandidate(
        "table", [page], [], [[Cell(clean_text(c)) for c in row] for row in rows], "cells"
    )
    candidate.inferred_columns = infer_columns(candidate.rows)
    for row in rows:
        for role, index in header_roles([clean_text(c) for c in row]).items():
            candidate.inferred_columns.setdefault(role, {"index": index, "confidence": 0.2})
    result = normalize(candidate, initial_type)
    return [
        ParsedLine(
            r.item_no,
            r.description,
            r.reference,
            r.unit,
            r.quantity,
            r.notes,
            "Other" if r.row_type == "UNKNOWN" else r.row_type,
            r.source_page,
            json.dumps(r.raw_text, ensure_ascii=False),
        )
        for r in result.rows
    ], result.warnings


def parse_pdf(path: Path, selected_id: str | None = None) -> PdfResult:
    from .pdf_pipeline import analyze

    try:
        doc, schedule, diagnostics, credible = analyze(path, selected_id)
        result = PdfResult(
            len(doc.pages), "\n\n".join(f"--- Page {p.number} ---\n{p.text}" for p in doc.pages)
        )
        result.diagnostics = diagnostics
        if not any(p.text.strip() for p in doc.pages):
            raise PdfImportError(
                "OCR_REQUIRED", "PDF neturi teksto sluoksnio. OCR dar nepalaikomas."
            )
        for page in doc.pages:
            if not page.text.strip():
                result.warnings.append(
                    {
                        "code": "PAGE_WITHOUT_TEXT",
                        "page": page.number,
                        "message": "Puslapis be teksto sluoksnio; OCR neatliekamas.",
                    }
                )
        if schedule is None:
            if not credible:
                error = PdfImportError(
                    "SCHEDULE_NOT_FOUND", "Nerasta struktūriškai tinkama kiekių lentelė."
                )
                error.result = result
                raise error
            result.needs_selection = True
            result.warnings.append(
                {
                    "code": "SCHEDULE_NEEDS_SELECTION",
                    "message": "Radome galimą sąnaudų lentelę. Patvirtinkite arba pasirinkite lentelę.",
                }
            )
            return result
        result.schedule = schedule
        result.warnings.extend(schedule.warnings)
        for row in schedule.rows:
            result.lines.append(
                ParsedLine(
                    row.item_no,
                    row.description,
                    row.reference,
                    row.unit,
                    row.quantity,
                    row.notes,
                    "Other" if row.row_type == "UNKNOWN" else row.row_type,
                    row.source_page,
                    json.dumps(
                        {
                            "cells": row.raw_text,
                            "bounds": row.source_bounds,
                            "candidate_id": schedule.candidate_id,
                            "confidence": row.extraction_confidence,
                            "row_type": row.row_type,
                        },
                        ensure_ascii=False,
                    ),
                )
            )
        result.pages = sorted({r.source_page for r in schedule.rows})
        return result
    except PdfImportError:
        raise
    except Exception as exc:
        code = str(exc) if str(exc) in {"PAGE_LIMIT", "INVALID_SELECTION"} else "INVALID_PDF"
        raise PdfImportError(
            code, "PDF nepavyko perskaityti arba lentelės pasirinkimas netinkamas."
        ) from exc
