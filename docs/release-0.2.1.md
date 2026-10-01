# 0.2.1 — bulk preparation workflow

Continues the existing Phase 10 implementation; no new architectural phase.

## Product changes

The normal path is import → review exceptions in the grid → TXT export. All
supported row types participate. Missing codes receive persistent editable custom
codes; compatible learned corrections and catalog evidence are reused. Source
descriptions, quantities and provenance remain separate from export fields.

Hierarchy, section identifiers and filenames receive persistent defaults. The
SISTELA parameter 89 lives in global settings. Advanced marker/NGR changes live
with the row. Readiness updates automatically. Manual transfer is available only
under **Papildomi būdai → Rankinis perkėlimas**; neither entered progress nor
per-row confirmation is required for the complete TXT package.

Migration 012 adds Equipment to the estimate constraint and extends the local
catalog search index to average-price entries and model references. Original
licensed files remain read-only and excluded from release bundles.

## Evidence and remaining acceptance

The actual `2024.07-616SR-BCB-AG.pdf` yields 12 rows: 11 materials and one work.
All receive codes. With the imported local historical/catalog knowledge, the fresh
browser regression reports 11 missing prices and three reserved-punctuation issues
(some concern the same row). No missing code or NGR entry is required. Prices are
not replaced with zero. Punctuation requires explicit output-text correction. Therefore
this unpriced source is not represented as a successfully exported real estimate.
The complete 12-row export regression uses clearly identified synthetic prices.

TXT follows the supplied manual but real SISTELA round-trip acceptance remains
pending. Current-project DBF export remains blocked by unresolved calculated
fields and identifier semantics. The isolated archive-clone experiment is not a
substitute for project export. See ADR 0011 for FACT/INFERENCE/UNKNOWN boundaries.

## Verification

234 backend tests passed with required private fixtures. The ordinary pytest
command intermittently stalled in Windows IPv4 socketpair creation before
application code. A temporary, untracked runner selected IPv6 for the test event
loop self-pipe; application and request logic were unchanged. 58 frontend tests and
15 Playwright tests passed: 307 total. The ordinary release PDF command also passed
52 tests. Ruff, frontend lint, TypeScript, production build and migration checks
passed. Actual frozen EXE tests and installer install/reinstall/uninstall checks
passed. Both 0.2.1 artifacts were generated; 0.2.0 hashes remain unchanged. See
release-0.2.1.json for hashes and release-0.2.1-files.md for changed files.

The standard IPv4 Playwright run passed all 15 tests. A later screenshot rerun
encountered intermittent local socket and file-write failures; screenshot
verification was repeated using an untracked IPv6 localhost harness with the
application's normal runtime-origin configuration. No networking workaround is
included in the production bundle.

Added regression coverage (13 backend, two frontend, two browser tests): stable
codes across reload/delete; all three supported row types; missing-price blocking;
average-price catalog export; compatible correction learning; full model-reference
matching; material historical provenance without copying old prices; stable section
codes; version-guarded advanced options; automatic readiness; global settings;
simplified bulk export; and the real PDF/catalog preparation path. The frozen EXE
smoke test also exports a complete priced 12-row fixture without manual transfer.

## Next real-world test

Darius supplies actual prices for custom positions, reviews output text and the
selected codes, and exports the entire prepared estimate once. In a disposable
SISTELA estimate, match parameter 89, load **Informacija pakete**, validate and
form the information. Compare all 12 codes, quantities, units, descriptions and
prices against the prepared grid; record any rejected record verbatim locally.
Do not use or measure manual-transfer completion for this acceptance.
