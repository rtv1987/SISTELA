# Antros iteracijos užbaigimas

2026-09-29. Tęstas esamas kodas. Repo pradžioje ir pabaigoje visi projekto failai
nesekami Git; commit bazės nėra, todėl tuščias `git diff` nereiškia, kad nebuvo
implementacijos. Nieko neperkurta ir originalūs pavyzdžiai nekeisti.

## Iki pertraukimo jau buvo

- Veikiantys 0–3 fazių API, SQLite, PDF parseris ir DBF analizės įrankiai.
- Capability modelis, PackageTextParser, analizės CLI, ADR 0004 ir formato tyrimas.
- React darbo lentelės, projektų, susiejimų skydelio, Entry Mode ir Excel komponentai.
- Transakcinio grid/undo, mapping istorijos, vienetų tikrinimo, XLSX adapterių ir
  migracijų 002/003 pagrindas.
- Pradinė patikra: 43 backend testai praėjo, Ruff ir frontend lint praėjo.
  Frontend testų nebuvo (`No test files found`). Tikras XLSX importavo 28 iš 30
  eilučių; UI darbo eiga naršyklėje dar nebuvo patikrinta.

## Šiuo tęsiniu užbaigta

- Excel skaičių importas tiesiogiai iš OOXML į Decimal, mokslinio žymėjimo
  palaikymas, apvalinimas iki 6 skaitmenų su įspėjimu ir originalo išsaugojimu.
  Tikras pvz.xlsx: 30 eilučių, 20 medžiagų / 10 darbų, 2 tikslumo įspėjimai.
- Blogų eilučių atmetimas ir aiškiai leidžiamas dalinis importas; antraštės ribų
  patikra; eksporto tikslumo ir formulėmis atrodančio teksto regresijos.
- Eilučių kopijos išlaiko originalaus dokumento nuorodą, puslapį ir raw duomenis.
  Kopijos netampa automatiškai patvirtintais normatyvais ar suvestomis eilutėmis.
- Escape atšaukia langelio juodraštį; nepavykusio išsaugojimo būsena rodoma aiškiai.
  Entry Mode klaviatūros įvykių apdorojimas veikia ir ne elemento įvykiams.
- Rankinis kodo pataisymas išvalo ankstesnio pasiūlymo įvertį. Patvirtinimų istorija
  išlieka po app perkūrimo, o naujesnis pataisymas turi prioritetą.
- Windows setup/dev/test skriptai apima frontend; izoliuotas Playwright serveris
  naudoja laikiną bazę, neliesdamas vartotojo projektų.
- Pridėta 15 backend, 14 frontend ir 3 naršyklės testai (32 nauji scenarijai).

## Keisti / pridėti failai šiame tęsinyje

- Backend: `backend/sistela/api.py`, `grid.py`, `mapping.py`, `schemas.py`,
  `spreadsheets.py`, `integration.py`.
- UI: `frontend/src/App.tsx`, `Grid.tsx`, `EntryMode.tsx`.
- Testai: `tests/test_workflow.py`, `tests/test_domain.py`, `tests/test_package.py`,
  `frontend/src/workflow.test.tsx`, `frontend/e2e/workflow.spec.ts`,
  `frontend/playwright.config.ts`.
- Paleidimas: `scripts/setup.ps1`, `dev.ps1`, `test.ps1`, `e2e_server.py`.
- Dokumentai: `README.md`, `frontend/README.md`, `docs/progress.md`,
  `docs/sistela-package-format.md`, `docs/decisions/0005-grid-history-and-excel.md`,
  `docs/iteration-02.md`.
- UI vaizdai: `docs/screenshots/estimate-grid.png`, `docs/screenshots/entry-mode.png`.

Ankstesnio bandymo migracijos, PackageTextParser, ExcelPanel, MappingPanel ir kiti
veikiantys failai išsaugoti; jų kūrimas nepriskiriamas šiam tęsiniui.

## Patikra

- Backend: **58 passed**, įskaitant tikrus PDF/XLSX/DBF ir senos bazės migraciją.
- Frontend: **14 passed** (Vitest/Testing Library).
- Naršyklė: **3 passed** (Chromium/Playwright): tikro PDF importas su kopijos
  atsekamumu; projekto kūrimas → redagavimas → normatyvas → Entry Mode → XLSX
  eksportas/importas; 500 eilučių paieška, masinis keitimas ir undo.
- Iš viso **75 testai**, be skip pateikus privačius originalus.
- Ruff, TypeScript, ESLint, Vite production build: sėkmingi.
- `alembic check`: modelių ir migracijų skirtumų nėra; `pip check`: klaidų nėra.
- Visų 9 originalių failų SHA-256 sutampa su manifestu.
- Liko trečiosios šalies Starlette TestClient/httpx deprecation įspėjimas;
  Playwright pateikia NO_COLOR/FORCE_COLOR aplinkos įspėjimą. Testai nuo to nekinta.

## UI

[Darbo lentelė](screenshots/estimate-grid.png): projektai kairėje, paieška ir filtrai,
grupuojamos redaguojamos eilutės, normatyvo pasirinkimas dešinėje. Plati lentelė
slenkama horizontaliai; šaltinio ir galutiniai pavadinimai lieka atskiri.

[Entry Mode](screenshots/entry-mode.png): dideli keturi perkeliami laukai, kopijavimo
mygtukai, klaviatūros navigacija, suvestų eilučių skaitiklis. Vaizduose tik
sintetiniai duomenys; TEST-N50 nėra tikro normatyvo rekomendacija.

## Ribos ir likęs MVP

- Istorinių DBF susiejimų importas su žmogaus patvirtinimo UI dar neįgyvendintas.
  Esami originalų skaitymo ir sd/dd analizės įrankiai išsaugoti.
- Package Text gramatika UNKNOWN; analizė EXPERIMENTAL; exporter sąmoningai
  neveikia ir neprijungtas prie API/UI. Realaus SISTELA round-trip įrodymo nėra.
- Nėra normatyvų katalogo validavimo, automatinio vienetų perskaičiavimo, OCR,
  automatinio suvedimo į SISTELA ar AI. Pasiūlymai tik iš vietinių patvirtinimų.
- Undo skirtas paskutiniam lentelės veiksmui; importo, mapping ir suvedimo veiksmų
  neatšaukia. Po vėlesnio tos eilutės pakeitimo undo grąžina konfliktą.
- XLSX nėra SISTELA formatas, formulės neskaičiuojamos. Vieno importo limitas 500
  eilučių; ilgesnius nei 6 dešimtainius skaičius importas apvalina su įspėjimu.
- UI optimizuota darbui Windows kompiuteryje; 500 eilučių scenarijus patikrintas.
  Vienu metu paleiskite tik vieną backend procesą tai pačiai duomenų bazei.

## Tikslus kitas rekomenduojamas darbas

PHASE 6: sukurti read-only istorinių DBF eilučių peržiūros/importo eigą naudojant
jau patikrintą sd/dd jungtį. Kiekvienam kandidatui rodyti failą, įrašą, kodą,
istorinį tekstą ir vienetą; tik aiškiai vartotojo patvirtintus kandidatus įtraukti
į mapping istoriją. Istorinio pervadinto teksto nepaversti originaliu katalogo
pavadinimu. Pridėti realių DBF regresiją ir Playwright patvirtinimo scenarijų.

Package Text tyrimas atskiras: gauti autentiškus vieno lauko pakeitimo pavyzdžius,
užfiksuoti SISTELA versiją ir patikrinti round-trip prieš svarstant writer.
