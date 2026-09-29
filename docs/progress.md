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

Liko 6 fazės istorinių DBF susiejimų peržiūra ir aiškus vartotojo patvirtinimas
prieš perkeliant į mapping istoriją. Esami DBF analizės įrankiai veikia read-only.
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
