# ADR 0009: Structure-first PDF schedules

Status: implemented; second production fixture and Windows release acceptance pending.

## Problem

The old importer only inspected a page after a regular expression matched a
quantity-schedule heading, or immediately after an already accepted page. It also
required recognized description/unit/quantity headers, tried text extraction only
when native extraction returned no rows, and classified every non-work row as a
material. This coupled discovery, interpretation and row classification.

## Decision

Use a local deterministic pipeline. `pdf_candidates.py` owns extraction;
`schedule.py` owns the extractor-independent cell/candidate/normalized-row models,
column profiling, evidence scoring and classification; `pdf_pipeline.py` owns
document-level deduplication, continuation and selection. `pdf.py` adapts a
NormalizedSchedule to existing estimate-line fields. `parse_table` is retained as
a compatibility adapter using the same semantic engine, not a second parser.

Every page enters cheap discovery. Pages with fewer than two numeric word tokens
do not undergo deeper table analysis. Remaining pages have three independent
candidate generators: pdfplumber ruled tables, PyMuPDF coordinate grids and loose
repeated description/unit/quantity rows. No heading, system, product, filename,
project identifier, physical page number or material/work ratio gates discovery.

Column confidence uses 80% observed values and 20% optional header hints. Profiles
cover text length, numeric density, increasing/consecutive item identifiers,
short repeated unit tokens and mixed alphanumeric references. Familiar units add
evidence; unfamiliar short tokens remain eligible. A single numeric column is not
assigned as an item-number column. Decimals remain Decimal throughout.

Scoring has explicit signed reasons for description/unit/quantity, repeated rows,
sequential items, references, sections, optional heading vocabulary and index
hints. Local table evidence penalizes contents, rooms, standards, fire matrices,
software, signature/title blocks and revisions. No work/material count appears
in the score. These are evidence scores, not calibrated probabilities.

Credible means score >= 0.55 with at least one valid item. Automatic selection
requires >= 0.78 and a margin > 0.12 over the next credible distinct region.
Otherwise the persisted import has `SCHEDULE_NEEDS_SELECTION`, zero inserted
lines, previews and selectable candidate IDs. Only the absence of credible
candidates produces `SCHEDULE_NOT_FOUND`. Rejected and duplicate candidates stay
in diagnostics. Overlapping regions are deduplicated using geometry and row
agreement, with native extraction preferred on equal scores.

Coordinate cells are clustered into visual rows and recurring x anchors. Adjacent
wrapped fragments join until a new item/quantity/header/section boundary. Adjacent
page candidates merge only with compatible semantic columns, horizontal bounds
and increasing item numbers, or a bottom-to-top continuation without item numbers.
Repeated headers disappear during normalization; section context survives merging.

Classification happens after selection: explicit section, semantic hints, then
unambiguous human-confirmed historical knowledge matching text/system/unit.
Unresolved types remain `UNKNOWN` in parser provenance and use existing `Other`
in storage. Existing Review Queue blocks these rows. Historical type knowledge
does not assign or confirm a SISTELA code.

## Persistence and safeguards

Existing ImportRun.options stores diagnostics, pending selection and selected ID;
no migration is needed. Source copies stay immutable and content-addressed.
Selection is scoped to project/import, validated against persisted candidate IDs,
claimed atomically, reparsed from the stored source, and cannot be submitted twice.
A parser-version mismatch cannot silently apply stale candidate IDs. Rows preserve
page, raw cells, bounds, candidate ID, score and classification evidence.

The UI shows page ranges, first five rows, inferred columns, counts and score
reasons. Reopening the application restores pending choices. No external service,
LLM, OCR, SISTELA automation or changes to DBF/Package Text policies are introduced.

## Limits and release gate

The first real GSS and synthetic PDFs are available. The requested second real
PDF has not been supplied; its tests skip explicitly in normal development and
fail with `--require-fixtures`. Synthetic PDFs never stand in for that acceptance.
Index numbers are optional physical-page hints; unknown printed-page offsets are
not assumed. Unusual spanning cells, heavily rotated text and unrecognized table
intent may need human selection or further evidence-backed improvements.

PyMuPDF 1.26.4 is pinned and included in Windows packaging. Its distribution is
AGPL/commercial licensed; the project must account for that dependency's license
when distributing binaries.

Version stays at the last release until **all** real regression gates pass. Then
the explicit patch decision is 0.1.1 in `backend/sistela/version.py`. The builder
refuses to replace existing versioned artifacts, requires real PDF regressions,
and verifies installer metadata, filenames, portable bytes and the actual frozen
runtime before writing checksums. Existing releases remain intact. Future bug
fixes/parser changes are patch releases; minor releases require an explicit decision.
