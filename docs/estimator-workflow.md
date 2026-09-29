# PHASE 7 — estimator review and manual SISTELA handoff

SISTELA Assistant prepares a working estimate and assists manual entry. It does
**not** perform verified automatic import into SISTELA or calculate a final
commercial estimate. DBF remains read-only. Package Text is experimental and
disabled in production handoff. No SISTELA folder writes, UI automation, external
telemetry or AI integration are present.

## Daily workflow

1. Create a project and import PDF or XLSX. Open **Peržiūra**.
2. Review Queue shows rows with issues, blocking rows first. Enable “Rodyti ir
   paruoštas eilutes” to include resolved rows. Materials can have quantity,
   source or price issues, but never require work codes.
3. Inspect suggestions and their historical evidence separately from the current
   project's filename, PDF page and raw extracted text. High/Medium/Low are text
   match labels, not probabilities. Historical rewritten descriptions are not
   catalogue originals. The original normative description stays blank if unknown.
4. Apply and explicitly confirm a suggestion, enter a different code, reject an
   individual suggestion, or mark the row for manual selection. Manual selection
   still requires a code and explicit confirmation before handoff.
5. If the project says `650 m` and the chosen norm says `100M`, review the preview
   `650 m → 6.5 × 100m` and press **Patvirtinti konversiją**. Select the conversion
   from an actual candidate's unit or enter the verified unit in **Normatyvo vienetas**.
   No conversion panel is shown for identical, incompatible or unknown target units;
   `100m` is never chosen as a generic default. Then confirm the code
   against the target unit. Only `m ↔ 100m` is supported. No automatic scaling.
6. Edit quantities, descriptions and prices in the existing grid. Keep both
   possible duplicates explicitly, or combine their quantities and delete the
   extra row manually. The normal grid undo remains available. Never auto-merge.
7. Open **Paruošta SISTELA** and press **Patikrinti parengtį**. Resolve all blocking
   issues. Warnings remain visible but do not block manual handoff.
8. Open **SISTELA Entry Mode**, place it beside SISTELA and copy each work's code,
   target quantity and description. Mark entered only after checking SISTELA.
9. Export the working XLSX as a review / backup / collaboration artifact.

## Validation and state

`workflow.validate_project_for_sistela(session, project_id)` is the shared service.
`GET /projects/{id}/validation` computes a read-only report; `POST .../validate`
also persists the derived project status. An empty project is blocking.

Blocking categories include missing work code, missing/nonpositive quantity,
unknown unit, unconfirmed mapping, unit mismatch, stale/unconfirmed conversion,
unknown row type and invalid descriptions. The MVP unit allowlist is m, 100m,
vnt., kompl., m2, m3, kg, t, val., l and km. Extend it deliberately when verified
project units require it; arbitrary matching strings do not establish safety.

Warnings include low text match, missing price, historical-only mapping evidence,
historical price reference, strong output/historical description differences and
possible duplicates. Duplicate candidates require at least 95% normalized text
similarity and identical section, system, type and normalized unit. Acknowledgments
are tied to the pair's identities and comparison fields; changed descriptions
reopen the warning. Source rows are never automatically removed.

Import sets `IMPORTED`; edits conservatively set `NEEDS_REVIEW`. Validation returns
`MAPPING_IN_PROGRESS` when codes exist but blocking issues remain, otherwise
`NEEDS_REVIEW`. Zero blockers permits `READY_FOR_SISTELA`; all work rows marked
entered yields `HANDED_OFF`. The last means the user's entry declarations, not
verification by SISTELA. The validation screen always computes current state.

Work lifecycle: `unmapped → suggested → confirmed`; explicit rejection produces
`rejected`, manual review or conversion produces `needs_review`. Selecting or
converting never confirms a norm. Confirmations continue using `SistelaMapping`
and `MappingConfirmation`, with optimistic row version checks.

## Conversion and prices

The `review_data.conversion` snapshot stores decimal strings `source_quantity`,
`source_unit`, `target_quantity`, `target_unit`, `conversion_rule`,
`confirmed_by_user` and `confirmed_at`. The project quantity is never overwritten.
Changing the source quantity or unit makes the stored conversion unconfirmed and
blocks entry/export of the stale target. Grid duplicates and project copies do
not inherit review approvals. Reconfirm the conversion, then the code. To choose a norm in the original project
unit again, explicitly cancel the conversion and reconfirm the norm.

Material prices remain independent of work codes. Price status is MISSING,
ENTERED, HISTORICAL_REFERENCE or CONFIRMED. Confirmation requires an entered price;
editing a price removes its confirmation. Historical prices are never copied
automatically. A reference status does not establish a current approved price.

## Entry Mode V2

Default scope: pending works, first not entered. Filters: all works, pending,
needs review, confirmed. The optional “Įtraukti medžiagas” retains the older
manual material-entry capability. Progress and percentage follow the chosen scope.

| Key | Action |
| --- | --- |
| Left / Right | Previous / next visible row |
| Enter | Mark entered and advance |
| Space | Toggle entered |
| C | Copy code only |
| Q | Copy target quantity only |
| D | Copy output description |
| Esc | Return to readiness summary |

Shortcuts ignore inputs, selects, textareas and editable text. Clipboard quantity
is a plain decimal with a period, no labels or unit, e.g. `6.5`, never `6,5 100M`.
Numbers are Decimal internally; JavaScript uses decimal.js. Clipboard permission
failure is displayed, with manual copy instructions. Actual acceptance of the
period separator must still be tested in the installed SISTELA version.

## Working XLSX

The first 13 existing columns keep their positions for compatibility. Appended
columns preserve section, SISTELA target unit and quantity, mapping state, price
state and explicit conversion validity. Existing columns retain project system,
type, description, technical reference, source unit/quantity, code, original and
output descriptions, separate material/work prices and notes.

Stale target quantities are blank, not silently recomputed. Text cannot execute as
Excel formulas. Values above Excel's 15 significant-digit limit are preserved as
text with an export warning. Decimal arithmetic does not introduce binary floats.
No SISTELA percentages, profit or margin calculations are reproduced. Reimport
uses the original project columns and deliberately requires fresh approvals; XLSX
is not a full database restore including review history.

## Local workflow statistics

Counts refer to current nondeleted project rows, not lifetime cumulative events:

- imported_line_count: rows with current-project document provenance;
- auto_suggested_mapping_count: works with suggestions; availability at a human
  review/confirmation action is stored so a new manual mapping does not count its
  own newly learned suggestion as saved work. Untouched works use current knowledge;
- confirmed_without_change_count / changed_mapping_count: currently confirmed
  rows with an applied suggestion retained / changed;
- manual_mapping_count: rows explicitly manual or confirmed without an applied
  suggestion;
- review_issue_count: current blocking and warning issue count, not row count;
- entry_mode_completed_count: work rows currently marked entered.

These local aggregates use persisted review choices, mapping confirmations and
entry timestamps. No document text is copied into a telemetry stream; no
keystrokes or external telemetry are collected. They are a first measurement of
workflow assistance, not a time-saving claim. Timing remains a manual field-trial
measurement.

## Real GSS evidence and next experiment

With only the provided historical DBF sample imported into a fresh test database,
the real GSS PDF gives **21 rows: 11 materials, 10 works**. **10/10 works** receive
at least one historical suggestion at the existing fuzzy threshold; **7/10** have
at least one unit-compatible candidate. Three need additional unit/candidate
review. All ten need a human mapping decision. Suggestion availability does not
prove any code is correct.

Backend and Playwright regressions import the real fixture, keep source provenance,
resolve explicit conversions, make test-only operator decisions, reach READY,
mark a work entered, reopen and export. Synthetic test codes are not catalogue
recommendations and are never embedded in production logic.

Next: Darius should use a **new disposable estimate in the real SISTELA UI** and
review the ten GSS work mappings against its actual catalogue. Start with one
`650 m → 6.5 × 100M` work, copy the code, `6.5` and description, and verify the
stored unit, quantity and text after saving/reopening SISTELA. Then enter the
remaining nine works while recording elapsed time, corrected codes, conversion
decisions and copy/keyboard problems. Compare against manual entry of the same
ten rows. Capture Assistant statistics before/after. This is a human-operated
experiment; DBF writes and Package Text production import remain prohibited.
