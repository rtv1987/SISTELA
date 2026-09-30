# Phase 10 implementation and acceptance report

## Preserved and completed

The resumed tree already contained the structural PDF parser, selection/provenance
UI, historical knowledge, explicit unit conversions, Entry Mode, XLSX, lifecycle
and Windows packaging. Catalog models/import/index and parts of automatic mapping
were in progress. Those changes were continued rather than recreated.

Completed: folder/ZIP catalog UI and offline search; schema/relationship discovery;
automatic work/material selection; persistent corrections partitioned by row type;
required-data readiness without mandatory mapping confirmation; a shared TXT/DBF
projection; documented experimental TXT generation and validation; persisted
parameter 89/hierarchy; unified export screen; minimal real-catalog TXT acceptance
artifact; regression tests and packaging checks. Original sources remain read-only.

Migrations: **009_normative_catalog**, **010_export_settings**,
**011_mapping_row_type**. Existing mapping rows migrate to Work; their codes and
history remain. Existing release artifacts are preserved.

## Evidence

Both private PDFs pass: old GSS **21 rows / 11 materials / 10 works**; new PDF
**12 / 11 / 1**, including a test with heading evidence removed. Ambiguous
schedules require an explicit persisted region choice. No fixture-specific
production rules were added.

The supplied catalog contains **296,285 normalized/reference records**, including
**35,035 work rates** and **88,576 resource relationships**. Twenty DBF schemas,
memo support, physical record provenance and original hashes are recorded.
See [catalog evidence](sistela-normative-catalog.md) for resolved counts and UNKNOWNs.

Latest user choices and relevant historical knowledge outrank generic catalog
matching. Compatible units rank first. A current catalog entry verifies existence
and original description. Unsupported or unknown units remain explicit blockers;
confidence alone does not block. Grid code corrections retain the previous
candidate, project/line, source/target units and timestamp. No extra confirmation
button is required after a selection. Explicit conversion remains mandatory.

TXT follows the documented supported subset of types 1/2/3/4/6 and existing-resource
type 7 adjustments. The generator parses its own output and compares exact target
quantities and codes. Type 7 financial/custom variants and undocumented escaping
remain blocked. Conservative text/price limits and encoding still need real-world
acceptance. [Format and parameter 89](sistela-package-txt.md).

**TEST_TXT:** `data/exports/TEST_TXT/TESTTXT.TXT`, 1 × N50-270, vnt., source
`erer.dbf` physical record 23,633. Requires actual SISTELA **89=0**. SHA-256:
`c3b8de042440735a2fa9d8da48e5d7f3e126d926bd7d818d0f6b0903fa7e8663`.
No quantity conversion is needed in this minimal fixture. For m↔100M, the
explicitly reviewed target quantity is exported once with 89=0. Unknown 89 blocks;
89=1 blocks scaled/converted quantities to avoid double conversion.

DBF golden clone remains technically proven; TEST_A_CLONE and TEST_B_ONE_CHANGE
were preserved. **New-project DBF generation remains blocked**, as allowed by the
specification: dd resource calculations, pd quantities/prices, td/od totals,
identifier collision/remapping and required new-archive fields are not established.
No new-project DBF artifact with fabricated zeroes was generated. Neither TXT nor
DBF has been claimed as accepted by Darius's real SISTELA.

## Automated verification

- Backend: **221 passed**, all real fixtures required, no skips.
- Frontend: **56 passed**.
- Playwright: **13 passed**; the new catalog/PDF/correction/TXT/DBF flow was rerun
  successfully after the final layout changes.
- **290 total tests**, including 29 new backend, four frontend and one browser test.
- Ruff, ESLint, TypeScript, Vite production build, Alembic schema comparison and
  `git diff --check` passed.
- Third-party deprecation notices remain (Starlette/httpx and PyMuPDF SWIG);
  they are not suppressed or test failures.

Screenshots (synthetic display data): [catalog](screenshots/phase10-catalog.png),
[export](screenshots/phase10-export.png). Existing review, Entry Mode, PDF selection,
Trash and DBF screenshots remain available.

## Darius: short acceptance procedure

1. In Settings, import your licensed normative folder or ZIP. Import a project PDF;
   check detected rows and source quantities.
2. Scan automatically populated codes. Change one code in the grid, reload and
   confirm the correction persists. Only review a conversion if units actually differ.
3. In a separate SISTELA test complex, set parameter 89=0. Paste TESTTXT.TXT via
   **Informacijos įvedimas → Informacija pakete**; run **Tikrinti informaciją →
   Formuoti sąmatinę informaciją**. Verify N50-270, quantity 1, unit vnt. Record the
   SISTELA version, messages and resulting row.
4. For DBF, use only the preserved clone/mutation tests in an isolated test context.
   Check equality and the single renamed text. Do not import these retained IDs
   over a live estimate. Report diagnostics; project DBF stays blocked pending
   the missing calculation/identifier evidence.

Do not promote either export capability based only on our tests. Real acceptance
is the next required external check; no subsequent phase is started.

## Release verification

Canonical version: **0.2.0**. Installer filename/PE version, portable EXE and
running `/app/info` agree. The actual frozen EXE ran with only Windows System32
on PATH, importing both real PDFs and the full normative folder, searching N50-270,
automatically selecting it, exporting TXT, cloning the golden DBF archive,
checking the project DBF blocker, restarting and preserving local data.

The actual installer passed install, installed launch, running-app reinstall,
uninstall and preservation of both user data and an unrelated file. This was an
isolated test on the current Windows PC, not a claim about a separate clean PC.
The portable was checked to contain no DBF, FPT, IDX, PDF or personal SQLite files.

The checksum finalization stage exposed a Windows PowerShell FileInfo-to-path
conversion bug after packaging and frozen verification had succeeded. The builder
now hashes `.FullName`; the corrected finalization stage passed under Windows
PowerShell. Neither release binary required alteration or rebuilding.

- `C:\Users\rtv19\Documents\GitHub\SISTELA\dist\windows\SISTELA-Assistant-Setup-0.2.0.exe`
  - 51,855,292 bytes
  - SHA-256 `34eccd8c44ff0009a17e6360aba4d84f13135885e18769a5b9514585d58b8d75`
- `C:\Users\rtv19\Documents\GitHub\SISTELA\dist\windows\SISTELA-Assistant-Portable-0.2.0.zip`
  - 67,628,735 bytes
  - SHA-256 `5daba92209f0392e89ac27c7af6d829e4762bec5cb5f8c71f264596f27fe9c5e`

Both 0.1.0 release hashes match their original values. No earlier release was
replaced. Checksums are also in `dist/windows/SHA256SUMS-0.2.0.txt`.

## Remaining limitations

Real SISTELA acceptance is pending for both exporters. New-project DBF generation
is explicitly blocked on mandatory unknown fields/formulas; no unsafe artifact is
claimed. TXT supports the documented experimental subset, with conservative
encoding/field limits and no guessed escaping or custom type-7 financial grammar.
The local lexical matcher is not an engineering judgment engine; Darius should
scan codes and correct exceptions. Unresolved units/relations remain visible.
Section/rate coefficient and type-7 adjustment options are advanced API features;
the normal UI covers the common hierarchy/rate/custom/equipment/parameter workflow.

## Files changed in this working tree

- `README.md`
- `backend/migrations/env.py`
- `backend/migrations/versions/009_normative_catalog.py`
- `backend/migrations/versions/010_export_settings.py`
- `backend/migrations/versions/011_mapping_row_type.py`
- `backend/sistela/api.py`
- `backend/sistela/auto_mapping.py`
- `backend/sistela/dbf_project.py`
- `backend/sistela/export_api.py`
- `backend/sistela/export_model.py`
- `backend/sistela/grid.py`
- `backend/sistela/history.py`
- `backend/sistela/integration.py`
- `backend/sistela/lifecycle.py`
- `backend/sistela/mapping.py`
- `backend/sistela/models.py`
- `backend/sistela/normative.py`
- `backend/sistela/normative_api.py`
- `backend/sistela/package_txt.py`
- `backend/sistela/services.py`
- `backend/sistela/spreadsheets.py`
- `backend/sistela/version.py`
- `backend/sistela/workflow.py`
- `docs/decisions/0010-normative-auto-export.md`
- `docs/pdf-schedule-detection.md`
- `docs/phase10-results.md`
- `docs/progress.md`
- `docs/release-0.2.0.json`
- `docs/screenshots/entry-mode.png`
- `docs/screenshots/estimate-grid.png`
- `docs/screenshots/historical-evidence.png`
- `docs/screenshots/historical-import.png`
- `docs/screenshots/pdf-schedule-selection.png`
- `docs/screenshots/phase10-catalog.png`
- `docs/screenshots/phase10-export.png`
- `docs/screenshots/phase7-entry.png`
- `docs/screenshots/phase7-ready.png`
- `docs/screenshots/phase7-review.png`
- `docs/screenshots/phase8-delete-confirmation.png`
- `docs/screenshots/phase8-trash.png`
- `docs/screenshots/phase9-dbf-experiment.png`
- `docs/sistela-auto-mapping.md`
- `docs/sistela-dbf-export.md`
- `docs/sistela-documentation-sources.json`
- `docs/sistela-export-architecture.md`
- `docs/sistela-normative-catalog.md`
- `docs/sistela-normative-schema.json`
- `docs/sistela-package-txt.md`
- `frontend/e2e/history.spec.ts`
- `frontend/e2e/workflow.spec.ts`
- `frontend/e2e/z_estimator.spec.ts`
- `frontend/e2e/zzz_dbf_export.spec.ts`
- `frontend/e2e/zzzz_phase10.spec.ts`
- `frontend/src/App.tsx`
- `frontend/src/Catalog.tsx`
- `frontend/src/DbfExport.tsx`
- `frontend/src/EntryMode.tsx`
- `frontend/src/Export.tsx`
- `frontend/src/Grid.tsx`
- `frontend/src/MappingPanel.tsx`
- `frontend/src/Workflow.tsx`
- `frontend/src/catalog-export.css`
- `frontend/src/catalog-export.test.tsx`
- `frontend/src/dbf-export.test.tsx`
- `frontend/src/estimator.test.tsx`
- `frontend/src/history.test.tsx`
- `frontend/src/lifecycle.test.tsx`
- `frontend/src/review-defects.test.tsx`
- `frontend/src/types.ts`
- `samples/manifest.json`
- `samples/normative-manifest.json`
- `scripts/build-windows.ps1`
- `scripts/create_txt_acceptance.py`
- `scripts/smoke_windows.py`
- `scripts/verify_windows_release.py`
- `tests/catalog_factory.py`
- `tests/test_domain.py`
- `tests/test_estimator.py`
- `tests/test_normative.py`
- `tests/test_package.py`
- `tests/test_package_txt.py`
- `tests/test_pdf_structure.py`
- `tests/test_workflow.py`
