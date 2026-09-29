"""Heading + header driven extraction. No page number, item or model constants."""

import json
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pdfplumber

from .common import clean_text, compact, normalize_text, normalize_unit, parse_decimal

PARSER_VERSION = "pdf-table-1.0"
logger = logging.getLogger(__name__)


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


def header_columns(row: list[str | None]) -> dict[str, int]:
    columns = {}
    for i, cell in enumerate(row):
        name = compact(cell or "")
        if "pavadin" in name or "aprasym" in name:
            columns["description"] = i
        elif "kiek" in name:
            columns["quantity"] = i
        elif "matovnt" in name or "matovien" in name or name in {"vnt", "vienetas"}:
            columns["unit"] = i
        elif "zymuo" in name or "model" in name:
            columns["reference"] = i
        elif "pastab" in name:
            columns["notes"] = i
        elif "pozic" in name or "eilnr" in name or name in {"nr", "poz"}:
            columns["position"] = i
    return columns


def parse_table(
    rows: list[list[str | None]], page: int, initial_type: str | None = None
) -> tuple[list[ParsedLine], list[dict]]:
    """Works with merged/null columns, arbitrary column order and multiline cells."""
    lines, warnings = [], []
    columns = {}
    category = initial_type
    inferred_warning = False
    for index, row in enumerate(rows, 1):
        header = header_columns(row)
        if {"description", "quantity", "unit"} <= header.keys():
            columns = header
            continue
        nonempty = [clean_text(c) for c in row if clean_text(c)]
        label = normalize_text(" ".join(nonempty))
        if len(nonempty) == 1:
            if label in {"medziagos", "iranga ir medziagos", "irenginiai ir medziagos"}:
                category = "Material"
                continue
            if label in {"montavimo darbai", "darbai", "montavimo ir derinimo darbai"}:
                category = "Work"
                continue
        if not columns:
            continue

        def cell(name):
            at = columns.get(name)
            return clean_text(row[at]) if at is not None and at < len(row) else ""

        description, unit, quantity = cell("description"), cell("unit"), cell("quantity")
        position = cell("position")
        if not description:
            continue  # Title blocks, blank rows, section labels and table captions.
        if not (unit or quantity) and not re.fullmatch(r"\d+[.)]?", position):
            continue
        if position and not re.fullmatch(r"\d+(?:[.\-]\d+)*[.)]?", position):
            continue
        try:
            parsed_quantity = parse_decimal(quantity)
            if parsed_quantity < 0:
                raise ValueError("Negative quantity")
            if not unit:
                raise ValueError("Missing unit")
        except ValueError:
            warnings.append(
                {
                    "code": "ROW_REJECTED",
                    "page": page,
                    "table_row": index,
                    "message": "Eilutės kiekis arba vienetas neįskaitomas; tikrinkite šaltinį.",
                }
            )
            continue
        line_type = category
        if line_type is None:
            line_type = (
                "Work"
                if re.search(r"montav|tiesim|derinim|programav", normalize_text(description))
                else "Material"
            )
            if not inferred_warning:
                warnings.append(
                    {
                        "code": "TYPE_INFERRED",
                        "page": page,
                        "message": "Blokas be tipo antraštės: medžiagų / darbų tipą patikrinkite.",
                    }
                )
                inferred_warning = True
        reference = cell("reference")
        if re.fullmatch(r"T\s*S\s*[\d\s.]+", reference, re.IGNORECASE):
            reference = re.sub(r"\s+", "", reference)
        lines.append(
            ParsedLine(
                position.rstrip(".)"),
                description,
                reference,
                normalize_unit(unit),
                parsed_quantity,
                cell("notes"),
                line_type,
                page,
                json.dumps(row, ensure_ascii=False),
            )
        )
    return lines, warnings


def is_schedule_heading(text: str) -> bool:
    text = normalize_text(text)
    return bool(re.search(r"(?:sanaudu\s+)?kiekiu\s+ziniarast", text))


def parse_pdf(path: Path) -> PdfResult:
    try:
        with pdfplumber.open(path) as pdf:
            if len(pdf.pages) > 300:
                raise PdfImportError("PAGE_LIMIT", "PDF viršija 300 puslapių ribą.")
            result = PdfResult(len(pdf.pages), "")
            texts = []
            previous_matched = False
            previous_type = None
            any_text = False
            for number, original_page in enumerate(pdf.pages, 1):
                page = original_page.dedupe_chars()
                text = page.extract_text() or ""
                texts.append(f"--- Page {number} ---\n{text}")
                any_text = any_text or bool(text.strip())
                if not text.strip():
                    result.warnings.append(
                        {
                            "code": "PAGE_WITHOUT_TEXT",
                            "page": number,
                            "message": "Puslapis be teksto sluoksnio; OCR neatliekamas.",
                        }
                    )
                heading = is_schedule_heading(text)
                if not heading and not previous_matched:
                    continue
                page_lines, page_warnings = [], []
                for settings in ({}, {"vertical_strategy": "text", "horizontal_strategy": "text"}):
                    for table in page.extract_tables(table_settings=settings):
                        found, warnings = parse_table(
                            table,
                            number,
                            previous_type if previous_matched and not heading else None,
                        )
                        page_lines.extend(found)
                        page_warnings.extend(warnings)
                    if page_lines:
                        break
                previous_matched = bool(page_lines)
                previous_type = page_lines[-1].line_type if page_lines else None
                result.warnings.extend(page_warnings)
                if page_lines:
                    result.pages.append(number)
                    result.lines.extend(page_lines)
                    logger.info(
                        "parser=%s page=%s rows=%s warnings=%s",
                        PARSER_VERSION,
                        number,
                        len(page_lines),
                        len(page_warnings),
                    )
            result.extracted_text = "\n\n".join(texts)
            if not any_text:
                raise PdfImportError(
                    "OCR_REQUIRED", "PDF neturi teksto sluoksnio. OCR dar nepalaikomas."
                )
            if not result.lines:
                raise PdfImportError(
                    "SCHEDULE_NOT_FOUND", "Nerasta skaitoma sąnaudų kiekių lentelė."
                )
            return result
    except PdfImportError:
        raise
    except Exception as exc:
        # Library errors may contain confidential document fragments.
        raise PdfImportError(
            "INVALID_PDF", "PDF nepavyko perskaityti; patikrinkite failą arba slaptažodį."
        ) from exc
