# PHASE 9 — DBF export evidence and contract

## Evidence recorded before writer implementation

**FACT (customer report, 2026-09-29):** these six exact golden files successfully
transfer an estimate between the customer's licensed SISTELA installations. This
proves the source archive, not the compatibility of newly serialized files.

**FACT (bytes):** the complete ordered schemas, widths, scales, counts, hashes and
metadata of every file are in [sistela-dbf-golden-schema.json](sistela-dbf-golden-schema.json).
The previous [analysis](sistela-dbf-analysis.md) remains authoritative for the proven
104 sd/dd eight-field joins and three nd estimate hierarchies; they are reused.

| Role | Fields | Rows | Header bytes | Record bytes | EOF |
|---|---:|---:|---:|---:|---|
| dd | 50 | 391 | 1896 | 617 | 1A |
| nd | 55 | 11 | 2056 | 449 | 1A |
| od | 16 | 0 | 808 | 439 | absent |
| pd | 24 | 143 | 1064 | 401 | 1A |
| sd | 45 | 104 | 1736 | 320 | 1A |
| td | 42 | 48 | 1640 | 342 | 1A |

All six are 0x30 Visual FoxPro, table flags 0, field flags 0, 263 zero backlink bytes.
Only C/N/D occur. LDID=3 conflicts with Lithuanian data: explicit cp1257 is required,
and the writer must preserve LDID=3 for this profile rather than silently changing it.
Header date bytes are `[26,9,24]`; preserve them verbatim (century interpretation is
UNKNOWN). Record dates in nd are independent. There are no deleted rows in this
sample; space=active, `*`=deleted must be preserved for every physical record.
Blank numeric/date cells remain absent values, not zero. Leading character spaces
(including in KOMPLEKSAS) are significant. Physical row and field order are preserved;
whether SISTELA permits reordering is UNKNOWN. Empty OD retains its full schema and
absent EOF marker. No memo/index flags are present in this six-file sample.

The format layout is corroborated by the original
[Visual FoxPro table structure documentation](https://vfphelp.com/help/html/465e7a94-51b7-4e0c-98f9-432864fe5bcc.htm).
SISTELA-specific behavior is established only from local evidence, not FoxPro docs.

## Required/optional and calculated fields

Clone requires **all six tables and every declared field**, including blanks and
unknowns. Business-required versus optional fields for new SISTELA estimates is
UNKNOWN. Do not infer optionality from an empty cell or empty OD.

Conservative, exhaustive classification rule (applies to every field):

- **INPUT:** proven hierarchy/position key fields, IKAINIS code, dd GRUP=10 PAVADIN
  and MATO_PAV, sd KIEKIS and its matching dd GRUP=10 KIEKIS. Existing values are
  facts; this does not authorize arbitrary changes to keys or quantities.
- **DERIVED_BY_ASSISTANT:** none of the persisted financial fields has a proven
  general formula. sd/dd join consistency is derived validation, not pricing.
- **RECALCULATED_BY_SISTELA:** none proven. An original archive importing successfully
  does not show whether a changed quantity recalculates its resources or totals.
- **UNKNOWN:** every other field, including dd resource KIEKIS/NORMA/KAINA/VERTE,
  sd IMLUMAS/UZMOKEST/MEDZIAG/MECHANIZ and secondary quantities, all pd resource
  quantities/prices and td/od totals, percentages, flags and coefficient fields.
  Preserve values exactly for clone. Zero is still an existing value, not permission
  to synthesize a default. The machine-readable analysis report classifies each field.

Concrete counterexample: N50-270 in this archive has quantity **115**, not the
current project's 28. dd record 175 has KIEKIS=193.2, KAINA=54.6, VERTE=1054.87;
simple multiplication gives 10548.72. Therefore a naive price-times-quantity update
would be wrong. Quantity mutation is a **BLOCKER** until resource, pd and td
dependencies and rounding are proven. The first TEST_B instead changes exactly one
nonfinancial dd header description, preserving every numeric value and key.

## Naming, keys and release gates

The filename suffix `25-04-14` resembles a date and also occurs in KOMPLEKSAS
` D25-04-14`; causality and SISTELA filename requirements are UNKNOWN. Clone and
controlled text mutation retain all six original filenames in separate new folders.
No unproven basename generator is used.

Clone deliberately preserves identifiers for equivalence. **Import it only into an
isolated test context**: existing identifier collision/replace behavior is UNKNOWN.
Project planning assigns a deterministic 10-character complex candidate, object and
estimate=1, ordered section/line/header-detail ordinals within field widths. It checks
against supplied reserved complex IDs; this cannot rule out unseen SISTELA IDs.
Whether SISTELA allocates/remaps IDs is UNKNOWN. These are planning candidates only,
not a verified SISTELA allocation protocol; project serialization remains blocked.

Historical DBF import remains **SUPPORTED / READ ONLY**. Generated archive export is
**EXPERIMENTAL**, with no live-directory access. Both TEST_A and TEST_B acceptance by
Darius is necessary for promotion; it is not sufficient for new-project pricing or
ID rules. No user-editable switch or automatic capability promotion exists.


## Phase 10 shared projection

The project planner now consumes `export_model.normalized_estimate`, also used by
the TXT exporter. Catalog data does not prove dd/pd financial formulas or td/od
totals. These remain explicit blockers. The UI option is **DBF eksportas**.
Existing TEST_A/TEST_B artifacts and original golden DBFs remain unchanged.
No new-project DBF acceptance artifact is claimed while those mandatory values
are unknown.
