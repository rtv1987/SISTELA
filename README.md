# Phase 10 / 0.2.0 workflow

Local PDF/XLSX import → automatic codes → edit exceptions → required-data checks
→ experimental TXT or DBF handoff. Entry Mode remains available. Original DBFs,
PDFs and licensed normative sources remain read-only and are never bundled.

- [Structural PDF detection](docs/pdf-schedule-detection.md)
- [Local normative catalog and schema evidence](docs/sistela-normative-catalog.md)
- [Automatic mapping and corrections](docs/sistela-auto-mapping.md)
- [TXT grammar, parameter 89 and acceptance](docs/sistela-package-txt.md)
- [Shared export model and explicit DBF blockers](docs/sistela-export-architecture.md)

In Settings, import your licensed normative folder or ZIP locally. No external AI
is used. Codes stay editable; no per-row mapping confirmation is required.
Explicit unit conversion still requires review. TXT and DBF remain EXPERIMENTAL
until real SISTELA acceptance; project DBF output is blocked where mandatory
financial/identifier semantics remain unknown. Do not use a test clone against
live estimates.

# SISTELA Assistant

Lokalus įrankis sąnaudų žiniaraščio paruošimui prieš suvedimą į SISTELA.
Tai nėra SISTELA skaičiavimo variklis ar jos kopija.

**Dabartinis etapas: PHASE 9 – eksperimentinis DBF round-trip.** PDF importas, redaguojama
lentelė, masiniai pakeitimai, vieno veiksmo undo, eilučių ir projektų kopijos,
patvirtintų normatyvų istorija ir pasiūlymai, SISTELA Entry Mode, XLSX importas ir
eksportas. DBF analizė read-only. Package Text – EXPERIMENTAL leksinė analizė;
eksportas blokuotas iki patvirtinto SISTELA round-trip. Veikia istorinių DBF sąmatų importas, kandidatų peržiūra, patvirtinimas / atmetimas
ir pasiūlymai su kilmės įrodymais.

Veikia Review Queue, blokuojančių klaidų / įspėjimų validacija, aiškus `m ↔ 100M`
patvirtinimas nekeičiant projekto kiekio, parengties santrauka, Entry Mode V2
klavišai ir išsaugoma suvedimo eiga, darbinis XLSX su atskirais tiksliniais kiekiais
bei vietinė darbo statistika. Automatinis importas į SISTELA dar nepatvirtintas.
[Darbo eiga ir bandymas su Dariumi](docs/estimator-workflow.md).

Istorinis DBF importas: **SUPPORTED / READ ONLY**. Veikia izoliuotas šešių DBF
klonavimo eksportas (**EXPERIMENTAL**) su schema, jungčių patikra ir manifestu.
Naujo projekto DBF ir kiekio mutacija blokuojami dėl neįrodytų skaičiavimų / ID taisyklių.
Entry Mode išlieka. [TEST_A / TEST_B ir Dariaus instrukcija](docs/sistela-dbf-roundtrip.md)
· [Formato faktai ir UNKNOWN](docs/sistela-dbf-export.md).

## END USER INSTALLATION — diegimas vartotojui

1. Paleiskite **SISTELA-Assistant-Setup-0.1.0.exe** ir pasirinkite **Diegti**.
2. Atverkite **SISTELA Assistant** iš meniu Pradžia. Programa atsidarys naršyklėje.
3. Sukurkite projektą ir importuokite dokumentą. Baigdami spauskite **Uždaryti programą**.

Administratoriaus teisių įprastam diegimui nereikia. Projektai ir istorija saugomi
`%LOCALAPPDATA%\SISTELA Assistant`; pašalinus ar atnaujinus programą duomenys lieka.
Šiukšlinėje projektą galima atkurti; galutiniam trynimui reikia įvesti jo pavadinimą.
Bendra SISTELA patirtis ir originalūs dokumentai nešalinami.
[Diegimas ir priėmimo sąrašas](docs/windows-packaging.md) · [Šiukšlinė](docs/project-lifecycle.md).

## DEVELOPER SETUP — Windows kūrėjo aplinka

Reikia Python 3.12+ su pip, Node.js 22 LTS, pnpm ir Git. Priklausomybės diegiamos iš interneto vieną kartą;
runtime dokumentų niekur nesiunčia ir API rakto nereikia.

```powershell
git clone <šio-repo-URL>
cd SISTELA
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

Jei Python nėra `py` launcher sąraše, nurodykite tikrą vykdomąjį failą:

```powershell
.\scripts\setup.ps1 -Python 'C:\Python312\python.exe'
```

Programa: **http://127.0.0.1:8000/**. API: `/health`; kontraktas `/openapi.json`.
`setup.ps1` įdiegia Python ir frontend priklausomybes, migracijas bei sukompiliuoja UI.
`dev.ps1` atnaujina UI build ir paleidžia vietinį serverį; `-SkipBuild` naudoja esamą build.
Interaktyvios Swagger UI dar nėra: vengiant CDN, ši versija neprašo išorinių JS/CSS.
Neleiskite daugiau nei vieno API proceso su tuo pačiu duomenų katalogu.

Alternatyvios komandos (iš repo šaknies):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m alembic upgrade head
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
.\.venv\Scripts\python.exe -m uvicorn sistela.api:create_app --factory --host 127.0.0.1 --port 8000
```

## Patikrinti tikrą GSS importą

Repo originalai yra privatūs ir ignoruojami Git. Pateikite juos repo šaknyje arba
atitinkamuose `samples/input` ir `samples/sistela` kataloguose. Originalų neperrašykite.
Kopijos/hashai aprašyti `samples/manifest.json`. LFS nereikalingas dėl dydžio;
pasirinktas lokalus saugojimas dėl konfidencialumo.

PowerShell su veikiančiu API (Windows `curl.exe`, ne `curl` alias):

```powershell
$project = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/projects `
  -ContentType 'application/json' -Body '{"name":"GSS projektas","system_type":"GSS"}'
curl.exe -s -F 'file=@2024-10-XX-TDP-GSS.pdf' "http://127.0.0.1:8000/projects/$($project.id)/imports/pdf"
Invoke-RestMethod "http://127.0.0.1:8000/projects/$($project.id)/lines"
Invoke-RestMethod "http://127.0.0.1:8000/projects/$($project.id)/imports"
```

Tikėtina: 21 eilutė iš 14 puslapio (11 Material, 10 Work), `needs_review`.
Visos eilutės `unmapped`, jokie pavyzdiniai SISTELA kodai nepriskiriami.
Kiekiai/kainos JSON pateikiami tekstu; `PUT /projects/{id}/lines/{line_id}` priima
visus redaguojamus laukus ir `version`, grąžina 409 jeigu eilutė jau pakeista.
Įvesties forma aprašyta `/openapi.json`; šaltinio ir audito laukai neredaguojami.

PDF limitas 25 MB / 300 puslapių. Skenuotas dokumentas grąžina `OCR_REQUIRED`.
POST importui grąžina sukurtą ImportRun (201); jo `status` būtina patikrinti:
`failed` nėra sėkmingas duomenų importas. Dalinės eilutės atšaukiamos.
Pakartotinis identiškas failas tame pačiame projekte – 409. Po nepavykusio importo
naudokite naują projektą; pakartojimo UI bus kuriamas vėliau.

## Testai ir analizė

```powershell
.\scripts\test.ps1
.\scripts\test.ps1 -RequireFixtures
pnpm --dir frontend exec playwright install chromium
.\scripts\test.ps1 -RequireFixtures -E2E
.\.venv\Scripts\python.exe scripts/inspect_sources.py
.\.venv\Scripts\python.exe scripts/analyze_dbf.py --encoding cp1257
```

Be privačių failų jų regresijos pažymimos skip; `-RequireFixtures` trūkumą laiko klaida.
Sintetiniai struktūros testai nepakeičia realaus GSS regresinio testo.
E2E paleidžia atskirą serverį su laikina SQLite baze; prieš testą atlaisvinkite 8000 portą.
UI kūrimui galima atskirai paleisti `pnpm --dir frontend dev` (5173 portas, API proxy).
Analizės tekstai/JSON rašomi tik į ignoruojamą `tmp/source-inspection/`.
DBF raportas pateikia visų 232 laukų schemas, pavyzdžius ir patikrintą sd/dd jungtį.
`cp1257` čia yra aiškus konkretaus archyvo pasirinkimas, ne universali taisyklė.

## Duomenys ir ribos

Numatytai `data/sistela.sqlite3` ir `data/documents/`. Kitas katalogas:
`$env:SISTELA_DATA_DIR = 'C:\SistelaData'` prieš migraciją/paleidimą.
`.env.example` dokumentuoja nustatymus; `.env` automatiškai neskaitomas.
Atsarginei kopijai sustabdykite API ir nukopijuokite visą katalogą.
Originalūs fixtures nenaudojami kaip darbinis katalogas.

- Kodo ir pavadinimų atskyrimas: project_description, sistela_code,
  sistela_original_description, output_description.
- Pinigai ir kiekiai: Decimal, SQLite tekstas, be float skaičiavimų.
- Vietinis AI provider išjungtas; niekas į išorę nesiunčiama.
- DBF/package writer blokuoti; jokio tiesioginio SISTELA keitimo.
- PDF parseris remiasi lentelės struktūra ir reikšmių profiliais; antraštė nėra būtina.
  Dviprasmišką rezultatą pasirinkite importo informacijoje. Žr.
  [PDF diagnostiką](docs/pdf-import-diagnostics.md) ir [ADR 0009](docs/decisions/0009-structure-first-pdf.md).
  Antrojo realaus PDF regresija ir Windows 0.1.1 leidimas laukia originalaus failo.
  Neaiškios eilutės ir numanomas tipas matomi importo diagnostikoje.

Daugiau: [šaltiniai](docs/source-analysis.md), [DBF analizė](docs/sistela-dbf-analysis.md),
[architektūra](docs/architecture.md), [domenas](docs/domain-model.md), [fazės](docs/progress.md).

## Darbo eiga

1. Sukurkite projektą ir importuokite PDF. Peržiūrėkite importo informaciją.
2. Redaguokite langelius; Tab palieka lauką ir išsaugo, Escape atšaukia juodraštį.
   Paieška, filtrai ir grupavimas padeda rasti eilutes. Pažymėtas eilutes galima
   masiškai keisti, kopijuoti ar trinti. Undo taikomas paskutiniam lentelės veiksmui.
3. Pasirinkite darbo eilutę. Dešinėje įveskite tikrą SISTELA kodą, žinomą originalų
   normatyvo pavadinimą ir patikrinkite vienetą. Patvirtinimas išsaugomas SQLite.
   Kitoje tokio paties darbo eilutėje atsiranda pasiūlymas; jį taikykite ir patvirtinkite.
4. Entry Mode kopijuokite kodą, galutinį pavadinimą, vienetą ir kiekį. Pažymėkite
   eilutę suvestą tik ją patikrinę SISTELA. Progresas išlieka po programos perkrovimo.
5. Excel importe pasirinkite lapą, antraštę ir kolonas. Galima įklijuoti tris kolonas:
   pavadinimas, vienetas, kiekis. XLSX eksportas skirtas darbo duomenims, ne SISTELA paketui.

Vienetai nekonvertuojami: `100m` nėra `m`. XLSX reikšmės apvalinamos iki 6 skaitmenų
po kablelio su įspėjimu ir originalo išsaugojimu. Formulės nevykdomos. Daugiau nei
15 reikšminių skaitmenų turintys skaičiai eksportuojami tekstu. Patvirtinimo ir
suvedimo būsenos per Excel neperkeliamos. Palaikoma iki 500 eilučių vienu importu.

[Package Text tyrimas](docs/sistela-package-format.md) ·
[Šios iteracijos ataskaita](docs/iteration-02.md)


## Istorinės SISTELA sąmatos (PHASE 6)

Kairėje pasirinkite „Istorinės SISTELA sąmatos“, įkelkite vieno archyvo sd/dd/nd
ir turimus pd/td/od DBF failus, pasirinkę cp1257 pateiktam rinkiniui. Peržiūrėkite
kandidatą, patikrinkite jo sistemą ir vienetą, patvirtinkite arba atmeskite.
Įrodymai atveriami tiek istorijoje, tiek dabartinės sąmatos pasiūlymuose.
Pakartotinis tų pačių pagrindinių failų importas duomenų nedubliuoja.

Po šios versijos atnaujinimo vykdykite `dev.ps1` – jis sukompiliuoja UI ir pritaiko
migraciją. Atsarginei kopijai prieš migraciją sustabdykite programą ir kopijuokite
visą data katalogą. [Importo taisyklės ir ribos](docs/historical-dbf-import.md),
[PHASE 6 ataskaita](docs/iteration-03.md).

### 0.2.1 bulk workflow

Normal transfer is Import → review exceptions → **TXT eksportas** or **DBF eksportas**.
**Rankinis perkėlimas** is an optional fallback under **Papildomi būdai**, not product
acceptance. Unmatched supported rows get stable editable custom codes and derived
metadata; missing real prices remain precise exceptions. Global parameter 89 and
persistent hierarchy defaults remove repeated export setup.
See [product workflow decision](docs/decisions/0011-bulk-product-workflow.md).

### 0.2.2 maintenance

The current maintenance work removes artificial TXT description blockers and
shows price evidence, while preserving real missing-price exceptions. It also
checks installation integrity and bundles SQLAlchemy's native modules and Python
fallbacks. See [the 12-row investigation and acceptance procedure](docs/release-0.2.2.md).
TXT remains the bulk path; Rankinis perkėlimas is optional fallback. Real SISTELA
acceptance and new-project DBF calculation semantics remain unproven.
