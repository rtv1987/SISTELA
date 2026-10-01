# 0.2.1 — Bulk transfer is the normal product workflow

This finishes the current product workflow; it is not a new integration architecture.
Import → review exceptions → TXT or DBF is the primary path. `Rankinis perkėlimas`
is an optional emergency fallback under `Papildomi būdai`. Its progress is retained
but never defines product acceptance, readiness, or completion.

## Preparation and knowledge

Work, material and equipment rows use compatible learned corrections, historical
evidence and the appropriate catalog tables. Material searches include `gaminiai`,
`resursai` and `samkainw`, including model/mark references. Average-price entries
are indexed on upgrade as well as new import. Low fuzzy material similarities
remain suggestions; they are not silently treated as equivalent devices.

Missing suitable codes receive persisted `A` (material), `W` (work), or `I`
(equipment) plus 15 hexadecimal characters derived from project/row identity.
All generated codes fit the documented 18-character alphanumeric field, are
checked against stored line/catalog codes, and cannot be renumbered by row order.
The documented 7000–7999 group recommendation concerns modifying the user's
normative database, which this app does not do. These are package-local user codes.
Editing a code learns a system/type/unit-compatible correction; no Apply+Confirm
sequence is required. Originals, source quantities and explicit conversions remain.

`resursai` norm codes are not automatically emitted as standalone average-price
positions: the manual documents different semantics. Such a match is retained in
provenance and a custom code is prepared. User-selected unsupported resource forms
remain explicit export exceptions.

## Derived metadata, not manufactured financial data

**FACT:** manual printed p.47 documents custom `6,...,<S,unit>,P=...,R=7,price,NGR`
and equipment `<I,unit>,I=price` forms. Printed p.48 lists NGR 12 as other materials.
**INFERENCE / policy:** generic custom material metadata defaults to S and NGR 12,
with `GENERIC_NGR_12` warning/provenance. Equipment defaults to I. A directly
documented catalog NGR is preferred when available. NGR4 is not assumed equivalent
to the manual's NGR field. Overrides live in advanced work-table row details.

**FACT:** average-price catalog positions have a documented `6,code,quantity` form
without an explicit price. **UNKNOWN:** omission or automatic zero pricing for an
unlisted custom position. The manual's discussion of zero prices in other periods
does not authorize inserting zero for an unknown price today. Thus a missing custom
price blocks exactly that field; the application never manufactures it. Historical
prices and undated/base catalog amounts are not silently promoted to current prices.

Project hierarchy, section codes, filename and current month get persisted defaults.
Generated hierarchy labels replace reserved punctuation and fit documented widths;
source/row descriptions are never silently rewritten. Parameter 89 is an explicit
global Unknown/0/1 setting under `Nustatymai → SISTELA`, reused by all projects.

## Readiness and UI

Opening export recalculates TXT validation. The primary API validation status now
means the selected TXT format can be generated, including legitimate custom rows.
The older POST validation operation remains for backward-compatible common-row
diagnostics; ordinary UI never calls it. DBF planning separately identifies its
actual unresolved financial/identifier/profile fields and per-unit catalog evidence.
The shared projection supplies both formats with the same codes and quantities.

All row-level editing belongs in the work table. Export contains bulk actions,
exception links, optional hierarchy settings and a technical preview. A valid
12-row package downloads without any `/entry` or mapping confirmation request.

TXT and new-project DBF acceptance in real SISTELA remain experimental. Clone-only
DBF verification is not a substitute for a new-project calculation profile.
