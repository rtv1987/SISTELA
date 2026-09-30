# Fazės ir patikra

## 0 – Repository bootstrap

Pradinė repo būklė: nėra commitų ir programos kodo. Šaltiniai pateikti darbo metu.
Sukurta struktūra, README, AGENTS.md, .gitignore, .env.example, Python paketas,
priklausomybių versijos, Windows setup/dev/test komandos. Originalai palikti vietoje.
Patikra: vietinė Python 3.12 venv sukurta, paketas įdiegtas editable režimu.

## 1 – Reverse engineering

Išanalizuoti 2 PDF, XLSX ir 6 DBF. Sukurti source-analysis ir sistela-dbf-analysis.
DBF aprašytos visos 232 laukų schemos ir pasirinktų laukų pavyzdžiai.
104 sd pozicijos atitinka 104 dd GRUP=10 įrašus pagal sudėtinį raktą, kodą ir kiekį.
PDF žiniaraščio 14 puslapis peržiūrėtas kaip atvaizdas.
Patikra: 9 pirminiai šaltinių testai praėjo, originalų SHA-256 nepakito.

## 2 – Domain + DB

7 domeno lentelės ir atskira Alembic versijos lentelė.
Project, SourceDocument, EstimateSection, EstimateLine, SistelaMapping, ImportRun,
Requirement. Decimal tekstinis saugojimas ir priklausymo projektui FK apribojimai.
Patikra: 4 pirminiai domeno testai praėjo; pakartotinė migracija, tikslūs dideli
Decimal skaičiai, nepriklausomi pavadinimai, foreign key ir float atmetimas.

## 3 – PDF parseris ir importo API

Struktūrinė antraščių paieška, linijų lentelės ir tekstinių ribų fallback,
tipų klasifikavimas, vienetų normalizavimas, originalūs langeliai ir dokumento tekstas.
Realaus GSS regresija: visos 21 eilutė, 11 medžiagų ir 10 darbų, puslapis 14.
Papildomi testai: kolonų tvarkos keitimas, kelių eilučių tekstas, dešimtainiai kiekiai,
neteisingų kiekių atmetimas, normatyvinio vieneto išlaikymas, netinkamas PDF.
API patikra: visas tikro PDF importas į SQLite, duomenų išlikimas po naujo app
sukūrimo, auditavimas, pasenusių redagavimų konfliktai, dalinio importo rollback,
pakartotinio failo apsauga ir lokalios kilmės tikrinimas.

## Antros iteracijos būsena (2026-09-29)

4 ir 5 fazės įgyvendintos: React lentelė, projektų/eilučių kopijos, autosave,
paieška, filtrai, masiniai pakeitimai, undo ir SQLite patvirtinimų istorija su
exact/normalized/fuzzy pasiūlymais bei vienetų suderinamumo tikrinimu.
Papildomai veikia SISTELA Entry Mode su išliekančiu progresu ir XLSX
importas/eksportas, kolonų susiejimas, lapo pasirinkimas bei clipboard.
Package Text turi read-only leksinę analizę; gramatika UNKNOWN, būsena EXPERIMENTAL.
DBF ir Package Text rašymas lieka užblokuoti.

Šioje antroje iteracijoje dar buvo likusi 6 fazė; ji užbaigta tolesnėje iteracijoje
(žr. naujausią įrašą žemiau). Esami DBF analizės įrankiai veikia read-only.
Išsami darbų, failų, patikrų ir ribų ataskaita: [iteration-02.md](iteration-02.md).

## Galutinė patikra (2026-09-28)

- `scripts/test.ps1 -RequireFixtures`: **38 passed**, 17.81 s, jokių praleistų testų.
- Ruff: visi patikrinimai praėjo.
- `alembic check`: nėra skirtumų tarp migracijos ir modelių.
- `pip check`: nėra sugadintų priklausomybių.
- `setup.ps1` atskiroje švarioje repo kopijoje su nauja venv: sėkmingas diegimas
  ir migracija. Be privačių failų tos kopijos testai: 27 passed, 10 skipped.
- `dev.ps1`: realiai paleistas Uvicorn Windows aplinkoje; `/health` grąžino
  `{"status":"ok","phase":"0-3","external_ai":false}`, OpenAPI kontraktas pasiekiamas.
  Po patikros serveris sustabdytas.
- Originalių 9 failų SHA-256 sutampa su manifestu.
- Vienas trečiosios šalies deprecation įspėjimas: Starlette TestClient praneša apie
  būsimą `httpx` → `httpx2` pakeitimą. Tai testavimo adapterio įspėjimas, ne testų klaida.

## 6 – istorinės DBF žinios (2026-09-29)

Veikia read-only archyvo importas, istorinės sąmatos ir pozicijos, kilmės įrodymai,
kandidatų peržiūra, patvirtinimas / atmetimas, agreguoti pasiūlymai ir vienetų apsauga.
Tikras rinkinys: 3 sąmatos, 104 pozicijos, 39 darbų kandidatai, 34 skirtingi darbų kodai.
Pradinė 75 testų patikra praėjo; galutinė – 103 (79 backend, 19 frontend, 5 Playwright).
Lint, TypeScript, build ir migracijos atitinka; originalai nepakeisti.
[Išsami ataskaita ir PHASE 7 užduotis](iteration-03.md).


## 7 – sąmatininko peržiūra ir rankinis perdavimas (2026-09-29)

Įgyvendinta bendra validacija ir Review Queue, normatyvų būsenos ir atmetimas,
aiškus m ↔ 100M patvirtinimas su atskiru tiksliniu kiekiu, parengties santrauka,
Entry Mode V2, vietinė statistika, darbinis XLSX ir tikro GSS E2E eiga.
Projekto kiekio keitimas anuliuoja konversijos patvirtinimą. Originalų kilmė išlaikyta.
DBF tebėra read-only, Package Text eksperimentinis ir gamybinėje eigoje blokuotas.
Migracija: 007_estimator_review. Nauji testai: 16 backend, 8 frontend, 2 Playwright.
Praėjo 129 testai (95 backend, 27 frontend, 7 Playwright), Ruff, ESLint, TypeScript,
build ir migracijų patikra. Originalių šaltinių SHA-256 patikros praėjo.
[Išsami ataskaita](iteration-04.md), [darbo eiga ir realus bandymas](estimator-workflow.md).


## PHASE 7 – pirmojo realaus bandymo klaidų pataisos (2026-09-29)

Taisytos tik dvi atkuriamos klaidos. N50-270 istorinio ir projekto detektorių
aprašymų tekstinis panašumas yra 28.32 %, todėl istorinis patvirtinimas buvo
atmetamas iki rikiavimo ties 45 % slenksčiu. Pirmenybė patvirtintai istorijai
anksčiau dar reikalavo tikslaus/normalizuoto aprašymo sutapimo. Istorinė būsena ir
auditas buvo išsaugomi teisingai; pasiūlymų API juos jau naudojo, o UI grįžtant iš
istorijos persikraudavo. Naujos SistelaMapping kopijos ar duomenų migracijos nereikia.

Dabar vartotojo atitikmenys turi pirmenybę prieš patvirtintą istorinę patirtį, ši –
prieš nepatvirtintus fuzzy kandidatus. Patvirtintos istorijos tos pačios sistemos
ir tinkamų vienetų kandidatai neatmetami vien dėl skirtingų formuluočių; žemas
teksto įvertis nekeičiamas. Rodoma „Patvirtinta istorinė patirtis“ ir esami įrodymai.
Projektas lieka unmapped, po pritaikymo suggested, po atskiro patvirtinimo confirmed.

Konversijos blokas anksčiau buvo besąlyginis visiems darbams su 100m numatytąja
būsena. Jis perkeltas prie konkretaus normatyvo vieneto: rodomas tik m ↔ 100m,
kai tikslas žinomas iš pasiūlymo arba vartotojas jį nurodė normatyvo lauke.
Vienodiems, nesuderinamiems ir nežinomiems vienetams blokas nerodomas.

Pridėta 10 backend ir 14 frontend testų / parametrizuotų atvejų bei 1 Playwright
regresija su tikru DBF ir „Detektorių montavimas“, grįžimu iš istorijos be puslapio
perkrovimo, įrodymais, paslėpta konversija, pritaikymu ir aiškiu patvirtinimu.
Keisti backend history.py / mapping.py; frontend MappingPanel.tsx, Workflow.tsx,
types.ts; pridėtas conversion.ts. Testai: tests/test_history.py,
frontend/src/review-defects.test.tsx, frontend/e2e/history.spec.ts ir esamo
z_estimator.spec.ts konversijos žingsniai. Atnaujintos historical-dbf-import.md,
estimator-workflow.md ir automatiškai atkuriami estimate-grid / phase7-review ekranai.

## PHASE 8 — Windows paketas ir projektų gyvavimo ciklas (2026-09-29)

Prieš tęsiant peržiūrėti necommitinti pakeitimai ir išsaugotos abi realaus bandymo
pataisos. Pradinė žalia bazė: 105 backend + 41 frontend + 8 Playwright = 154 testai;
Ruff, TypeScript/ESLint, UI build ir Alembic patikra praėjo.

Įgyvendintas windowless PyInstaller x64 vykdomasis failas, produkcinis React UI,
vieno proceso localhost runtime su laisvu portu, automatinis naršyklės atvėrimas,
per-user AppData katalogai, migracijos su SQLite backup, versija, logų atvėrimas ir
uždarymo mygtukas. NSIS diegiklis su Start Menu / neprivaloma Desktop nuoroda ir
duomenis išsaugančiu uninstaller. Viena build komanda sukuria tikrą Setup, portable
ZIP ir SHA256SUMS; artefaktai ignoruojamame `dist/windows/`.

Projektai turi soft delete (migracija `008_project_trash`), šiukšlinę, atkūrimą ir
galutinio ištrynimo patvirtinimą tiksliu pavadinimu. Globali mapping/DBF patirtis
lieka. Bendros kopijos išsaugomos, kol jas naudoja kitas projektas; originalūs failai
nešalinami. Ankstesnės normatyvų prioriteto ir konversijų pataisos nepakeistos.

Pridėta 11 backend testų, 5 frontend ir 2 Playwright testai. Rezultatas:
**116 backend + 46 frontend + 10 Playwright = 172**, įskaitant tikrus privačius
GSS/DBF mėginius. Ruff, TypeScript, ESLint, Vite build ir Alembic schema check praeina.
Lieka bibliotekos Starlette/httpx deprecation įspėjimas; testų praleidimų nėra.
Du atskiri smoke scenarijai tikrina patį EXE bei tikrą diegimą/perinstaliavimą/
pašalinimą izoliuotuose duomenyse. Tai papildomos priėmimo patikros, ne į 172
įskaičiuoti pytest/Vitest/Playwright testai.

PHASE 8 pakeisti / pridėti failai:

- `backend/sistela/{api,db,grid,models,schemas,services}.py`;
  nauji `desktop.py`, `paths.py`, `version.py`, `lifecycle.py`;
  `backend/migrations/versions/008_project_trash.py`.
- `frontend/src/App.tsx`, nauji `Lifecycle.tsx`, `lifecycle.css`, `lifecycle.test.tsx`;
  `frontend/e2e/zz_lifecycle.spec.ts`, `frontend/package.json`.
- `packaging/{windows.spec,windows_launcher.py,installer.nsi,requirements-build.txt,END-USER.txt}`;
  `scripts/build-windows.ps1`, `scripts/smoke_windows.py`, `scripts/smoke-installer.py`;
  `pyproject.toml`, `tests/test_desktop_lifecycle.py`.
- `README.md`, `docs/windows-packaging.md`, `docs/project-lifecycle.md`,
  `docs/decisions/0007-windows-runtime-and-project-trash.md`, šis failas;
  nauji `docs/screenshots/phase8-trash.png`, `phase8-delete-confirmation.png` ir
  esami automatiškai atnaujinti demonstraciniai UI ekranai su nauja navigacija.

Švarus Dariaus Windows kompiuteris šiame seanse nepasiekiamas. Kitas konkretus
veiksmas: perduoti Setup ir SHA256SUMS, atlikti `windows-packaging.md` priėmimo sąrašą
paprasto vartotojo paskyroje. Diegiklis kol kas nepasirašytas; nėra online update.
Realiame update teste perinstaliuojama ta pati 0.1.0, nes ankstesnio išleisto Setup
nėra; schemos 007 → 008 backup atskirai patikrintas backend testu. Kita produkto
fazė nepradėta.

## PHASE 9 — isolated DBF round-trip experiments (2026-09-29)

Started from clean git status and a green 172-test baseline (116 backend, 46
frontend, 10 Playwright). The customer now verifies that the original six-file
archive is valid SISTELA interchange. AGENTS' prior blanket writer prohibition
was updated to reflect this explicit authorization; original/live files stay protected.

Implemented:

- `dbf_archive.py`: independent, read-only physical FoxPro C/N/D model, strict cp1257,
  Decimal/date/blanks, deleted flags, metadata and row order, schema analysis,
  established sd/dd/nd validation and exact semantic difference locations.
- `dbf_export.py`: separate SistelaDbfExporter, explicit fixed-width serialization,
  pre-publication reparse/comparison, new isolated export folder, SHA-256 manifest;
  six-table ROUND_TRIP_CLONE and bounded developer-only text mutation.
- `dbf_project.py`: source/target-aware project preparation, review/width/precision
  checks, separate descriptions/code, deterministic **proposed** identifiers with
  known historical complex collision checks. Actual PROJECT_EXPORT remains BLOCKED.
- `dbf_export_api.py`: six-file clone ZIP endpoint, project plan and explicit 409
  for unproven project generation. `DbfExport.tsx`: experimental warning, file
  selection/download and readable blocking explanation. Entry Mode unchanged.
- `scripts/compare_dbf_archives.py`, `scripts/dbf_roundtrip.py`, plus frozen-runtime
  smoke extended to exercise clone and the project-export gate.

Generated `data/exports/TEST_A_CLONE` and `TEST_B_ONE_CHANGE`, and ZIPs for Darius.
A is SAME, including all six original SHA-256 hashes. B has exactly one normalized
difference: dd physical record 174 PAVADIN gains ` [TEST_B]`. All numeric values,
keys and the other five DBFs remain identical. Original files retain golden hashes.
Both packages include manifest, schema/classification analysis, comparison and instructions.

The requested preferred quantity mutation is **not implemented**: dependent
resource/pd/td calculations are UNKNOWN. The numeric mutation utility fails closed.
No project DBFs are synthesized with guessed totals, unit IDs or identifiers. A
project input plan is not a working project serializer. These explicit remaining
limitations require SISTELA evidence; see `docs/sistela-dbf-export.md` and the
before/after quantity experiment in `docs/sistela-dbf-roundtrip.md`.

Tests added: 40 backend cases, 3 frontend and 1 real-fixture Playwright. Total:
**156 backend + 49 frontend + 11 Playwright = 216 passing**. Ruff, TypeScript,
ESLint, production frontend build, migration check pass. No migration added.
Starlette/httpx deprecation warning remains. New screenshot:
`docs/screenshots/phase9-dbf-experiment.png`.

Other changed files: `api.py`, `integration.py`, `ports.py`, `Workflow.tsx`,
`workflow.css`, capability regression assertions in `test_package.py` and
`test_workflow.py`; README, architecture, historical import, analysis and progress
documentation; ADR 0008 and the full 232-field golden schema JSON. Existing
demonstration screenshots are refreshed by Playwright.

Release gate: generated DBF **EXPERIMENTAL**; source historical import **SUPPORTED /
READ ONLY**; Package Text export still blocked. Actual SISTELA A/B acceptance is
PENDING. Next real action: Darius imports A and B in separate safe test contexts,
then supplies before/after archives for a quantity change made inside SISTELA.

Windows build regenerated successfully. Final EXE smoke passed actual PDF/DBF,
clone ZIP (six hashes identical), project-export 409 gate, restart and lifecycle.
Actual install/reinstall/uninstall smoke also passed with retained DB and unrelated
files. Setup: 37,063,280 bytes, SHA-256
`c8a72afebb80b9af32ca76a07b6aa8e3ac13de5ce6807a946d611bafffaf8147`.
Portable package contains no private DBF/PDF/XLSX/SQLite files. The existing
clean-machine limitation remains; real SISTELA itself was not run in this session.


## Structure-first PDF importer — 2026-09-30

Implemented the architectural refactor without overwriting the interrupted PHASE 9
work. Removed the exact-heading early gate, mandatory recognized-header dependency,
native-first-only fallback coupling and default-to-Material classification.

New parser modules: `backend/sistela/parsers/pdf_candidates.py`, `pdf_pipeline.py`,
`schedule.py`; `pdf.py` is now an application compatibility adapter. Updated unit
normalization in `common.py`. Three extractors (pdfplumber/native, PyMuPDF/geometry,
loose repeated rows), data-led columns, signed diagnostics, overlap deduplication,
wrapped rows, adjacent-page continuation and explicit selection are implemented.
Unknown types remain review-blocking; compatible confirmed historical knowledge
can classify them without confirming a SISTELA mapping.

Persistence/UI changes: `services.py`, `schemas.py`, `api.py`,
`frontend/src/App.tsx`, `types.ts`, new `PdfDiagnostics.tsx`. Existing ImportRun.options
holds previews/diagnostics and pending selection, so no migration was added.
Selection is project-scoped, source-hash checked and claimed atomically; repeat or
stale-parser selection is rejected. Source geometry and classification provenance
are retained per line.

Tests: new `tests/pdf_factory.py`, `tests/test_pdf_structure.py`,
`frontend/src/pdf-diagnostics.test.tsx`, `frontend/e2e/zz_pdf_structure.spec.ts`;
legacy mocked PDF tests in `tests/test_pdf.py` now create real PDF bytes. Coverage
includes all A–P presentation families, eight negative table categories, optional
index hints, independent loose extraction, unknown/conflicting historical types,
selection reload/ownership/source integrity and duplicate-submission rejection.

Validation: **190 backend passed, 2 skipped; 52 frontend passed; 12 Playwright
passed = 254 passing**. Ruff, frontend lint/TypeScript/build, Alembic check and
PowerShell build-script syntax passed. Earlier focused PDF/API rerun: 57 passed,
2 explicit missing-fixture skips. The strict PDF fixture run reports the two
missing-file failures rather than silently accepting them. Existing dependency
Starlette/httpx and PyMuPDF SWIG deprecation warnings remain.

The original real GSS remains **21 / 11 Material / 10 Work**, including a test that
removes heading/index evidence. Screenshot:
`docs/screenshots/pdf-schedule-selection.png` (synthetic data, visually reviewed).

Release preparation: pinned PyMuPDF in pyproject/requirements-lock, bundled it in
`packaging/windows.spec`, added immutable versioned-artifact guards and real PDF
regressions to `scripts/build-windows.ps1`, created `verify_windows_release.py`,
and extended `smoke_windows.py` to both real PDFs. The gate checks canonical
version against installer filename/resource, portable bytes and actual runtime.

**NOT DONE / external blocker:** `2024.07-616SR-BCB-AG.pdf` is still not supplied.
Its permanent tests expect 12 / 11 / 1, exact quantities/units and heading-independent
selection, but have not been executed against the original. No original fixture
or manifest hash has been fabricated. Version remains **0.1.0** until both real
regressions pass, per the release instruction. No new 0.1.1 installer/portable or
SHA exists yet. Old 0.1.0 artifacts were verified unchanged:
Setup c8a72afebb80b9af32ca76a07b6aa8e3ac13de5ce6807a946d611bafffaf8147;
Portable 29e08cf599866dc499049a8953a9d7f1fe914c7af3f9bd617dada12ff0982abb.

Next: obtain the exact missing PDF in repository root or samples/input, record
its SHA-256 in samples/manifest.json, run strict full regressions, fix any actual
structural discrepancy, then explicitly set VERSION=0.1.1 and build/verify both
Windows artifacts. See ADR 0009 for algorithm and known layout limitations.
