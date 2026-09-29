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
