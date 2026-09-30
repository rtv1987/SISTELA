"""Extractor-independent schedule evidence, inference and normalization.

Scores describe evidence, not statistical probabilities. No project vocabulary,
filenames, page positions or material/work ratios participate in selection.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal
from statistics import mean

from .common import clean_text, compact, normalize_text, normalize_unit, parse_decimal


@dataclass
class Cell:
    text: str
    bounds: tuple[float, float, float, float] | None = None


@dataclass
class TableCandidate:
    id: str
    pages: list[int]
    bounds: list[tuple[float, float, float, float]]
    rows: list[list[Cell]]
    extraction_method: str
    row_pages: list[int] = field(default_factory=list)
    inferred_columns: dict = field(default_factory=dict)
    score: float = 0
    score_reasons: list[dict] = field(default_factory=list)
    outcome: str = "REJECTED"
    row_count: int = 0


@dataclass
class ScheduleRow:
    item_no: str
    description: str
    reference: str
    unit: str
    quantity: Decimal
    notes: str
    row_type: str
    source_page: int
    source_bounds: list
    raw_text: list[str]
    extraction_confidence: float


@dataclass
class NormalizedSchedule:
    candidate_id: str
    confidence: str
    rows: list[ScheduleRow]
    warnings: list[dict]


UNIT_WORDS = {
    "vnt",
    "kompl",
    "kpl",
    "m",
    "m2",
    "m3",
    "100m",
    "kg",
    "t",
    "km",
    "val",
    "h",
    "pora",
    "por",
    "rinkinys",
    "l",
    "m2",
    "m3",
}


def number(value):
    try:
        return parse_decimal(clean_text(value))
    except ValueError:
        return None


def unit_strength(value):
    value = clean_text(value)
    if compact(value) in UNIT_WORDS:
        return 1.0
    # Unfamiliar short repeated unit tokens remain eligible for human review.
    return 0.55 if re.fullmatch(r"[^\W\d_][\w²³./%-]{0,9}", value) else 0.0


def header_roles(row):
    roles = {}
    for i, text in enumerate(row):
        name = compact(text)
        for role, pattern in (
            ("DESCRIPTION", r"pavadin|apras|description|itemdescription"),
            ("QUANTITY", r"^kiek|^qty$|^quantity$"),
            ("UNIT", r"^(mato|mat)?vnt$|^matovien|^vienetas$|^unit$"),
            ("REFERENCE_OR_MODEL", r"zymuo|model|^tipas$|^marke$|technspec|^poz$"),
            ("NOTES", r"pastab|gamintoj|komentar|notes"),
            ("ITEM_NO", r"eilnr|^nr$|pozic|^no$"),
        ):
            if re.search(pattern, name):
                roles[role] = i
                break
    return roles


def is_header(row):
    roles = header_roles(row)
    # A description may itself contain "description", "quantity" or "notes".
    # Real numeric cells are data evidence, not repeated-column-header evidence.
    return (
        len(roles) >= 2
        and bool({"DESCRIPTION", "QUANTITY"} & roles.keys())
        and not any(number(v.rstrip(".)")) is not None for v in row if v)
    )


def infer_columns(rows):
    width = max((len(r) for r in rows), default=0)
    headers = {}
    for row in rows[:6]:
        roles = header_roles([c.text for c in row])
        if is_header([c.text for c in row]):
            headers.update(roles)
    data = [
        r for r in rows if not is_header([c.text for c in r]) and sum(bool(c.text) for c in r) >= 2
    ]
    profiles = []
    for i in range(width):
        values = [r[i].text for r in data if i < len(r) and r[i].text]
        nums = [number(v.rstrip(".)")) for v in values]
        integers = [n for n in nums if n is not None and n == int(n)]
        increasing = sum(b > a for a, b in zip(integers, integers[1:])) / max(1, len(integers) - 1)
        consecutive = sum(b == a + 1 for a, b in zip(integers, integers[1:])) / max(
            1, len(integers) - 1
        )
        profiles.append(
            {
                "QUANTITY": mean([number(v) is not None for v in values]) if values else 0,
                "UNIT": mean([unit_strength(v) for v in values]) if values else 0,
                "DESCRIPTION": mean(
                    [min(len(v) / 30, 1) if number(v) is None else 0 for v in values]
                )
                if values
                else 0,
                "ITEM_NO": (len(integers) / max(1, len(values)))
                * (0.6 * increasing + 0.4 * consecutive),
                "REFERENCE_OR_MODEL": mean(
                    [bool(re.search(r"[A-Za-z].*\d|\d.*[A-Za-z]", v)) for v in values]
                )
                if values
                else 0,
            }
        )
    result, used = {}, set()
    # Value evidence contributes 80%; optional headers disambiguate correlated columns.
    for role in ("DESCRIPTION", "UNIT", "ITEM_NO", "QUANTITY", "REFERENCE_OR_MODEL", "NOTES"):
        choices = [
            (0.8 * p.get(role, 0) + 0.2 * (headers.get(role) == i), i)
            for i, p in enumerate(profiles)
            if i not in used
        ]
        if not choices:
            continue
        confidence, i = max(choices)
        threshold = 0.6 if role == "ITEM_NO" else 0.38
        if role in headers and headers[role] not in used:
            hinted = headers[role]
            hinted_score = 0.8 * profiles[hinted].get(role, 0) + 0.2
            if hinted_score >= confidence or role == "NOTES":
                confidence, i = hinted_score, hinted
        # A single numeric column is quantity, never a required item number.
        if role == "ITEM_NO" and (
            "QUANTITY" not in headers and sum(p["QUANTITY"] >= 0.6 for p in profiles) < 2
        ):
            continue
        if confidence >= threshold or role in headers and role == "NOTES":
            result[role] = {"index": i, "confidence": round(confidence, 3)}
            used.add(i)
    return result


def section_type(text):
    text = normalize_text(text)
    if text in {
        "medziagos",
        "iranga",
        "iranga ir medziagos",
        "irenginiai ir medziagos",
        "kabeliai",
        "papildomos medziagos",
    }:
        return "Material"
    if text in {"darbai", "montavimo darbai", "montavimo ir derinimo darbai"}:
        return "Work"
    return None


def classify(description, context):
    if context:
        return context
    text = normalize_text(description)
    if re.search(
        r"montav|irengim|klojim|tiesim|programav|derinim|paleidim|demontav|bandym|\bdarb", text
    ):
        return "Work"
    if re.search(
        r"kabel|vamzd|modul|akumul|detektor|irengin|itais|siren|rele|medziag|prietais|jungikl|siurbl|voztuv|varzt|komplekt",
        text,
    ):
        return "Material"
    return "UNKNOWN"


def normalize(candidate, initial_type=None):
    cols = candidate.inferred_columns
    output, warnings = [], []
    context = initial_type
    inferred = False
    if not {"DESCRIPTION", "UNIT", "QUANTITY"} <= cols.keys():
        return NormalizedSchedule(candidate.id, "LOW", [], [])
    for idx, cells in enumerate(candidate.rows):
        raw = [c.text for c in cells]
        nonempty = [v for v in raw if v]
        page = candidate.row_pages[idx] if candidate.row_pages else candidate.pages[0]
        if len(nonempty) == 1 and section_type(nonempty[0]):
            context = section_type(nonempty[0])
            continue
        if is_header(raw):
            continue

        def value(role):
            pos = cols.get(role, {}).get("index", len(raw))
            return raw[pos] if pos < len(raw) else ""

        description, unit = value("DESCRIPTION"), value("UNIT")
        quantity, item = number(value("QUANTITY")), value("ITEM_NO")
        if not description or not re.search(r"[^\W\d_]", description):
            continue
        if not unit or quantity is None or quantity < 0:
            if item and re.fullmatch(r"\d+[.)]?", item):
                warnings.append(
                    {
                        "code": "ROW_REJECTED",
                        "page": page,
                        "message": "Eilutės kiekis arba vienetas neįskaitomas; tikrinkite šaltinį.",
                    }
                )
            continue
        if not context and not inferred:
            warnings.append(
                {
                    "code": "TYPE_INFERRED",
                    "page": page,
                    "message": "Blokas be tipo antraštės: medžiagų / darbų tipą patikrinkite.",
                }
            )
            inferred = True
        reference = value("REFERENCE_OR_MODEL")
        if re.fullmatch(r"T\s*S\s*[\d\s.]+", reference, re.IGNORECASE):
            reference = re.sub(r"\s+", "", reference)
        output.append(
            ScheduleRow(
                item.rstrip(".)"),
                description,
                reference,
                normalize_unit(unit),
                quantity,
                value("NOTES"),
                classify(description, context),
                page,
                [list(c.bounds) for c in cells if c.bounds],
                raw,
                candidate.score,
            )
        )
    return NormalizedSchedule(
        candidate.id, "HIGH" if candidate.score >= 0.78 else "MEDIUM", output, warnings
    )


def score_candidate(candidate, nearby="", index_hint=False):
    candidate.inferred_columns = infer_columns(candidate.rows)
    schedule = normalize(candidate)
    candidate.row_count = len(schedule.rows)
    reasons = []

    def evidence(code, weight):
        if weight:
            reasons.append({"code": code, "weight": round(weight, 3)})

    for role, weight in (("DESCRIPTION", 0.23), ("UNIT", 0.23), ("QUANTITY", 0.24)):
        evidence(role, weight * candidate.inferred_columns.get(role, {}).get("confidence", 0))
    evidence("REPEATED_ROWS", min(candidate.row_count / 4, 1) * 0.18)
    evidence(
        "SEQUENTIAL_ITEMS",
        0.08 * candidate.inferred_columns.get("ITEM_NO", {}).get("confidence", 0),
    )
    evidence("REFERENCE_COLUMN", 0.025 if "REFERENCE_OR_MODEL" in candidate.inferred_columns else 0)
    evidence(
        "SECTION_CONTEXT",
        0.06 if any(section_type(" ".join(c.text for c in r)) for r in candidate.rows) else 0,
    )
    text = normalize_text(nearby)
    evidence(
        "SCHEDULE_VOCABULARY", 0.035 if re.search(r"ziniarast|sanaud|quantit|schedule", text) else 0
    )
    evidence("INDEX_HINT", 0.09 if index_hint else 0)
    # Local table/header evidence only: a nearby unrelated heading cannot veto a table.
    header = normalize_text(" ".join(c.text for r in candidate.rows[:2] for c in r))
    for code, pattern in (
        ("CONTENTS", r"turinys|dokumentu sudet|puslap|lapu skaic"),
        ("ROOM_AREAS", r"patalp|room|plotas|area"),
        ("STANDARDS", r"standart|normatyvin|normative"),
        ("REQUIREMENTS", r"technini.*reikalav|technical requirement|parametr|leistin"),
        ("FIRE_MATRIX", r"atsparum|resistance"),
        ("SOFTWARE", r"programine iranga|software|licenc"),
        ("TITLE_SIGNATURE", r"paras|signature|pareigos|atestato"),
        ("REVISION", r"laida|keitimu|revision|pakeitimo data"),
    ):
        evidence(code, -0.45 if re.search(pattern, header) else 0)
    evidence("NO_VALID_ROWS", -0.8 if not candidate.row_count else 0)
    candidate.score = round(max(0, min(1, sum(r["weight"] for r in reasons))), 3)
    candidate.score_reasons = reasons
    candidate.outcome = (
        "CREDIBLE" if candidate.row_count and candidate.score >= 0.55 else "REJECTED"
    )
    return candidate


def diagnostic(candidate):
    normalized = normalize(candidate)
    return {
        "id": candidate.id,
        "pages": candidate.pages,
        "bounds": candidate.bounds,
        "extraction_method": candidate.extraction_method,
        "inferred_columns": candidate.inferred_columns,
        "score": candidate.score,
        "score_reasons": candidate.score_reasons,
        "outcome": candidate.outcome,
        "row_count": candidate.row_count,
        "preview": [
            {"description": r.description, "unit": r.unit, "quantity": str(r.quantity)}
            for r in normalized.rows[:5]
        ],
    }
