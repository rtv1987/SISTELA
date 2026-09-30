"""Independent native, coordinate-grid and loose-row candidate generators."""

import re
from dataclasses import dataclass, field

import pdfplumber
import pymupdf

from .common import clean_text, normalize_text
from .schedule import Cell, TableCandidate, number, unit_strength


@dataclass
class ParsedPage:
    number: int
    text: str
    width: float
    height: float
    words: list = field(default_factory=list)


@dataclass
class ParsedDocument:
    pages: list[ParsedPage] = field(default_factory=list)
    candidates: list[TableCandidate] = field(default_factory=list)


def visual_rows(words):
    rows = []
    for word in sorted(words, key=lambda w: (w[1], w[0])):
        if not rows or abs(word[1] - rows[-1][0][1]) > 3:
            rows.append([word])
        else:
            rows[-1].append(word)
    return [sorted(row, key=lambda w: w[0]) for row in rows]


def groups(row):
    cells = []
    for w in row:
        if cells and w[0] - cells[-1].bounds[2] < 13:
            last = cells[-1]
            last.text += " " + w[4]
            last.bounds = (
                last.bounds[0],
                min(last.bounds[1], w[1]),
                w[2],
                max(last.bounds[3], w[3]),
            )
        else:
            cells.append(Cell(w[4], tuple(w[:4])))
    return cells


def text_grid(words, page):
    """Discover recurring cell x anchors, then join wraps within item boundaries."""
    rows = [groups(row) for row in visual_rows(words)]
    # Cheap discovery requires repeated split rows, independent of title/known units.
    plausible = [r for r in rows if len(r) >= 3 and any(number(c.text) is not None for c in r)]
    if len(plausible) < 2:
        return []
    blocks, block = [], []
    for row in rows:
        if block and row[0].bounds[1] - block[-1][0].bounds[3] > 45:
            blocks.append(block)
            block = []
        block.append(row)
    if block:
        blocks.append(block)
    candidates = []
    for block in blocks:
        seeds = [r for r in block if len(r) >= 3 and any(number(c.text) is not None for c in r)]
        if len(seeds) < 2:
            continue
        anchors = []
        for row in seeds:
            for cell in row:
                x = cell.bounds[0]
                match = next((a for a in anchors if abs(a[0] - x) < 12), None)
                if match:
                    match[1] += 1
                else:
                    anchors.append([x, 1])
        starts = sorted(a[0] for a in anchors if a[1] >= max(2, len(seeds) * 0.35))
        if len(starts) < 3 or len(starts) > 10:
            continue
        aligned = []
        for row in block:
            cells = [Cell("") for _ in starts]
            for cell in row:
                i = min(range(len(starts)), key=lambda j: abs(starts[j] - cell.bounds[0]))
                if cells[i].text:
                    cells[i].text += " " + cell.text
                    b = cells[i].bounds
                    cells[i].bounds = (
                        min(b[0], cell.bounds[0]),
                        min(b[1], cell.bounds[1]),
                        max(b[2], cell.bounds[2]),
                        max(b[3], cell.bounds[3]),
                    )
                else:
                    cells[i] = cell
            aligned.append(cells)
        from .schedule import infer_columns, is_header, section_type

        roles = infer_columns(aligned)
        qty = roles.get("QUANTITY", {}).get("index")
        item = roles.get("ITEM_NO", {}).get("index")
        if qty is None:
            continue
        joined = []
        for row in aligned:
            text = [c.text for c in row]
            boundary = is_header(text) or section_type(" ".join(text))
            new_item = item is not None and bool(re.fullmatch(r"\d+[.)]?", row[item].text))
            if joined and not boundary and not new_item:
                prior_qty = number(joined[-1][qty].text)
                this_qty = number(row[qty].text)
                # A row with a new quantity is a new item unless the previous item
                # is still incomplete. Continuations may contain model/notes too.
                prior_header = is_header([c.text for c in joined[-1]]) or section_type(
                    " ".join(c.text for c in joined[-1])
                )
                if not prior_header and (this_qty is None or prior_qty is None):
                    for i, cell in enumerate(row):
                        if cell.text:
                            previous = joined[-1][i]
                            previous.text = clean_text(previous.text + " " + cell.text)
                            if previous.bounds and cell.bounds:
                                a, b = previous.bounds, cell.bounds
                                previous.bounds = (
                                    min(a[0], b[0]),
                                    min(a[1], b[1]),
                                    max(a[2], b[2]),
                                    max(a[3], b[3]),
                                )
                            else:
                                previous.bounds = cell.bounds
                    continue
            joined.append(row)
        coords = [c.bounds for r in aligned for c in r if c.bounds]
        bounds = (
            min(c[0] for c in coords),
            min(c[1] for c in coords),
            max(c[2] for c in coords),
            max(c[3] for c in coords),
        )
        candidates.append(TableCandidate("", [page], [bounds], joined, "geometry"))
    return candidates


def loose_rows(words, page):
    """Independent fallback for compact lines without stable column anchors."""
    blocks, current = [], []
    for row in visual_rows(words):
        texts = [w[4] for w in row]
        quantity = number(texts[-1]) if texts else None
        if len(texts) >= 3 and quantity is not None and unit_strength(texts[-2]) >= 0.55:
            prefix = texts[:-2]
            item = prefix.pop(0) if re.fullmatch(r"\d+[.)]?", prefix[0]) else ""
            bounds = (row[0][0], min(w[1] for w in row), row[-1][2], max(w[3] for w in row))
            current.append(
                [
                    Cell(item, bounds),
                    Cell(" ".join(prefix), bounds),
                    Cell(texts[-2], tuple(row[-2][:4])),
                    Cell(texts[-1], tuple(row[-1][:4])),
                ]
            )
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return [
        TableCandidate(
            "",
            [page],
            [(b[0][0].bounds[0], b[0][0].bounds[1], b[-1][-1].bounds[2], b[-1][-1].bounds[3])],
            b,
            "loose",
        )
        for b in blocks
        if len(b) >= 2
    ]


def discover(path):
    document = ParsedDocument()
    with pymupdf.open(path) as geometry, pdfplumber.open(path) as native:
        if len(geometry) > 300:
            raise ValueError("PAGE_LIMIT")
        for i, page in enumerate(geometry):
            words = page.get_text("words", sort=True)
            text = page.get_text("text", sort=True)
            document.pages.append(ParsedPage(i + 1, text, page.rect.width, page.rect.height, words))
            # All pages enter discovery. Expensive native geometry only for pages
            # with multiple numbers and multiple visual rows, never title gating.
            if sum(number(w[4].rstrip(".)")) is not None for w in words) < 2:
                continue
            for table in native.pages[i].dedupe_chars().find_tables():
                rows = [
                    [Cell(clean_text(text), cell) for text, cell in zip(texts, row.cells)]
                    for texts, row in zip(table.extract(), table.rows)
                ]
                document.candidates.append(
                    TableCandidate("", [i + 1], [table.bbox], rows, "native")
                )
            document.candidates.extend(text_grid(words, i + 1))
            document.candidates.extend(loose_rows(words, i + 1))
    for i, candidate in enumerate(document.candidates):
        candidate.id = f"table-{candidate.pages[0]}-{i + 1}"
        candidate.row_pages = [candidate.pages[0]] * len(candidate.rows)
    return document


def index_hints(document):
    hints = set()
    for page in document.pages:
        for line in page.text.splitlines():
            text = normalize_text(line)
            # Token families are evidence only, never an eligibility gate.
            if re.search(r"ziniarast|schedule|quantit|sanaud", text):
                match = re.search(r"\b(\d{1,3})\s*$", text)
                if match:
                    hints.add(int(match[1]))
    return hints
