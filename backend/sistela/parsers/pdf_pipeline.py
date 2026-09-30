"""Deterministic document-level selection, independent from application storage."""

from .pdf_candidates import discover, index_hints
from .schedule import diagnostic, normalize, score_candidate


def overlap(a, b):
    if a.pages != b.pages:
        return False
    x, y = a.bounds[0], b.bounds[0]
    area = max(0, min(x[2], y[2]) - max(x[0], y[0])) * max(0, min(x[3], y[3]) - max(x[1], y[1]))
    return area / max(1, min((x[2] - x[0]) * (x[3] - x[1]), (y[2] - y[0]) * (y[3] - y[1]))) > 0.65


def row_keys(candidate):
    return {(r.item_no, r.unit, r.quantity) for r in normalize(candidate).rows}


def same_region(a, b):
    if a.pages != b.pages:
        return False
    x, y = a.bounds[0], b.bounds[0]
    intersection = max(0, min(x[2], y[2]) - max(x[0], y[0])) * max(
        0, min(x[3], y[3]) - max(x[1], y[1])
    )
    union = (x[2] - x[0]) * (x[3] - x[1]) + (y[2] - y[0]) * (y[3] - y[1]) - intersection
    return intersection / max(1, union) >= 0.8


def analyze(path, selected_id=None):
    doc = discover(path)
    hints = index_hints(doc)
    for c in doc.candidates:
        # Only text above the candidate is a heading hint.
        page = doc.pages[c.pages[0] - 1]
        top = c.bounds[0][1]
        nearby = " ".join(w[4] for w in page.words if top - 100 <= w[1] < top)
        score_candidate(c, nearby, c.pages[0] in hints)
    # Keep diagnostics for every extractor, but suppress duplicate selection choices.
    credible = []
    for c in sorted(
        doc.candidates, key=lambda c: (c.score, c.extraction_method == "native"), reverse=True
    ):
        if c.outcome != "CREDIBLE":
            continue
        duplicate = next(
            (
                a
                for a in credible
                if same_region(c, a)
                or (
                    overlap(c, a)
                    and len(row_keys(c) & row_keys(a))
                    / max(1, min(len(row_keys(c)), len(row_keys(a))))
                    >= 0.7
                )
            ),
            None,
        )
        if duplicate:
            c.outcome = f"DUPLICATE:{duplicate.id}"
        else:
            credible.append(c)
    # Adjacent pages continue only when semantic columns, horizontal geometry,
    # and item sequence agree. Adjacency or a repeated heading alone is insufficient.
    merged = []
    for c in sorted(credible, key=lambda c: (c.pages[0], c.bounds[0][1])):
        prior = merged[-1] if merged else None
        arows, brows = (normalize(prior).rows if prior else []), normalize(c).rows
        sequence = bool(
            arows
            and brows
            and arows[-1].item_no.isdigit()
            and brows[0].item_no.isdigit()
            and int(brows[0].item_no) > int(arows[-1].item_no)
        )
        columns = prior and {k: v["index"] for k, v in prior.inferred_columns.items()} == {
            k: v["index"] for k, v in c.inferred_columns.items()
        }
        geometry = (
            prior
            and abs(prior.bounds[-1][0] - c.bounds[0][0]) < 20
            and abs(prior.bounds[-1][2] - c.bounds[0][2]) < 20
        )
        page_boundary = (
            prior
            and prior.bounds[-1][3] > doc.pages[prior.pages[-1] - 1].height * 0.8
            and c.bounds[0][1] < doc.pages[c.pages[0] - 1].height * 0.3
            and not arows[-1].item_no
            and not brows[0].item_no
        )
        if (
            prior
            and c.pages[0] == prior.pages[-1] + 1
            and columns
            and geometry
            and (sequence or page_boundary)
        ):
            prior.pages.extend(c.pages)
            prior.bounds.extend(c.bounds)
            prior.rows.extend(c.rows)
            prior.row_pages.extend(c.row_pages)
            prior.row_count += c.row_count
            c.outcome = f"CONTINUATION:{prior.id}"
        else:
            merged.append(c)
    ranked = sorted(merged, key=lambda c: c.score, reverse=True)
    chosen = next((c for c in ranked if c.id == selected_id), None) if selected_id else None
    if selected_id and chosen is None:
        raise ValueError("INVALID_SELECTION")
    if (
        not chosen
        and ranked
        and ranked[0].score >= 0.78
        and (len(ranked) == 1 or ranked[0].score - ranked[1].score > 0.12)
    ):
        chosen = ranked[0]
    if chosen:
        chosen.outcome = "SELECTED"
    return (
        doc,
        normalize(chosen) if chosen else None,
        [diagnostic(c) for c in doc.candidates],
        bool(ranked),
    )
