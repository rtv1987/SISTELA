# Shared SISTELA export projection

`export_model.normalized_estimate` projects persisted project lines and export
settings into one hierarchy/section/row structure. Both the TXT generator and
DBF project planner consume it. It preserves source and output descriptions,
selected code/type, separate source and target quantities/units, explicit
conversion validity, actual entered price, catalog reference and provenance.
Decimal text crosses the API boundary; exporters do not recompute mappings or
unit conversions. DBF planning retains additional schema-specific diagnostics.

Common review validates quantity, row type, units, code and explicit conversions.
TXT adds hierarchy, record syntax/ordering, widths, required custom financial
inputs and parameter 89. DBF adds golden schema/encoding/scale checks and
unresolved mandatory calculation/identifier blockers. Warnings and absence of a
legacy CONFIRMED state do not alone block an otherwise valid row.

Global parameter 89 and per-project hierarchy/section/row options are persisted
in `export_settings`. Project settings are removed on permanent project deletion;
global catalog and reusable mapping knowledge survive. Migrations 009–011 add
the catalog/FTS index, settings and work/material knowledge partition. Existing
mapping rows become Work without changing their codes or history.

The UI exposes "Eksportuoti į SISTELA", "TXT eksportas" and "DBF eksportas".
TXT creates a new UUID export folder, never overwriting originals; download,
clipboard preview and opening the exports folder are available. DBF retains
the proven clone experiment and explicit new-project blocker. Neither exporter
writes into a SISTELA working folder. Entry Mode and XLSX remain alternatives.

FACT: six-file golden cloning is technically byte-equivalent and originals stay
unchanged. UNKNOWN: regenerated/new-project SISTELA acceptance, mandatory dd/pd
resource calculations, td/od totals and external identifier collision rules.
The full normative catalog provides references, not proof of those formulas.
No new-project DBF file is created using guessed zeroes or financial values.
