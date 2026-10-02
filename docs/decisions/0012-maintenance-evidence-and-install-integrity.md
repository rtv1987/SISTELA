# 0012 — 0.2.2 evidence and installation integrity

Maintenance of 0.2.1, not a new architectural phase.

## Package requirements

**FACT:** the supplied SISTELA manual, printed pp.46–48, documents existing
catalog positions as `6,code,quantity`; custom positions as
`6,code,quantity,<S,unit>,P=description,R=7,price,NGR`; equipment uses `<I,unit>`
and `I=price`. Type 7 identifies a resource below a parent position. On p.48 its
price is supplied when different from the corresponding file; an absent resource
requires all fields. This does not prove that a raw production-resource code can
be substituted for a standalone type 6 average-price position.

**Policy:** A = catalog price evidenced for the exact selected period; B = a
documented existing catalog position needing no explicit package price; C = custom
position with documented explicit-price syntax; D = unproven representation.
A/B never acquire an artificial missing-price blocker. Historical prices are not
current prices. D gets a representation/evidence exception, not a price demand.
Catalog base-price fields without a proven period are not promoted to current
prices. A records the exact KAIYYMM column; it does not invent an amount.

**FACT:** the manual gives 120-character limits for hierarchy labels, not `P=`
row descriptions. The former 120-character row cap was our conservative assumption
and is removed. **Policy/inference:** whitespace normalization, decimal comma →
decimal point, and list comma → semicolon avoid record delimiters without dropping
words or changing numeric values. Source/output text remains untouched; the TXT
projection exposes original text, prepared text and transformation rules.
Other reserved characters remain precise exceptions. Long-text acceptance in real
SISTELA is still **UNKNOWN**; no silent truncation is introduced.

**UNKNOWN:** whether zero-priced custom positions can be imported and priced later.
ZERO022.TXT is a separately labelled, explicitly requested acceptance experiment;
its zero is never applied to real project rows. There is no documented omitted-price
custom variant, so no such importable file is fabricated.

## Matching

Shared words alone must not automatically select a narrower work scope. Full-text
similarity or a strong model match is required for automatic catalog selection.
Existing automatic work matches with weak full-text evidence are flagged at export;
explicit user decisions remain intact. Wrong capacity, material, diameter or missing
accessories cannot be resolved by lowering confidence thresholds.

## Packaging findings and remedy

**FACT:** the affected local folder contained 36 files. Its EXE hash matches the
0.2.0 portable; 520 of that release's 556 files are absent, including the entire
SQLAlchemy directory. A copied reproduction fails to create runtime state. The
complete original 0.2.1 portable includes all eight SQLAlchemy native modules and
boots from a clean external folder on this PC.

The immediate cause is an incomplete local deployment, not evidence that the 0.2.1
archive omitted `_collections_cy`. **UNKNOWN:** why the older extraction/installation
stopped; disk exhaustion is plausible but not proven.

Collect SQLAlchemy's runtime modules, native extensions and upstream Python sources
(excluding testing), so all distributed `_cy` modules have fallbacks. Do not collect
the entire environment. A SHA-256 installation manifest and frozen SQLite/dynamic
import check must pass before the installer reports success. Repair uses the new
bundle's shutdown path, independent of a damaged installed copy. Database imports
are deferred until normal startup, keeping shutdown dependency-light.

Portable acceptance extracts outside the repo, supplies only a Windows environment,
boots twice, checks migrations/health/UI/liveness/persistence, and then faults all
native SQLAlchemy extensions in the disposable copy to exercise upstream fallbacks.
Installer acceptance covers install, launch, running-app upgrade, damaged-module
repair, relaunch and uninstall with user data preserved. Previous releases and the
affected local installation remain untouched during these tests.
