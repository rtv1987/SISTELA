# Architektūra

## Sprendimas

Viena lokali aplikacija: React/TypeScript/Vite lentelė → FastAPI → SQLAlchemy → SQLite.
Python 3.12+, pdfplumber teksto ir struktūrinių lentelių ištraukimui, openpyxl Excel,
dbfread skaitymui su Decimal skaitinių laukų parseriu, RapidFuzz istoriniams ir patvirtintiems pasiūlymams.
Veikia React lentelė, Entry Mode, XLSX mainai ir istorinių DBF žinių peržiūra.
Jokių Tauri, mikroservisų ar debesies priklausomybių.

## Ribos

- `parsers`: gryni duomenų ištraukimo moduliai, nežino apie DB ar HTTP.
- `models`, `db`: domenas, tikslios Decimal reikšmės, įjungti SQLite foreign keys.
- `services`: projekto operacijos ir audituojamas importas.
- `api`: validuoti HTTP kontraktai; dešimtainiai skaičiai JSON eilutėmis.
- `ports`: SistelaExporter, AiMappingProvider. Nepatvirtinti eksportai išmeta
  aiškią NotImplementedError, nieko nerašo.
- `scripts`: read-only šaltinių analizė ir Windows paleidimas.

## Importo eiga

Projektas → riboto dydžio PDF įkėlimas → SHA-256 → lokali šaltinio kopija →
SourceDocument + ImportRun(running) → parseris → viena transakcija skyriams ir eilutėms →
ImportRun(completed/needs_review/failed). Nepavykęs importas palieka audito įrašą,
bet ne dalinę sąmatą. Pakartotinis to paties failo importas į tą patį projektą
atmetamas, kad eilutės netyčia nesidubliuotų.

Originalūs langeliai saugomi `source_raw_text` kaip JSON, visas ištrauktas dokumento
tekstas – SourceDocument. Puslapiai 1-based. Klasifikavimo įspėjimai nesutampa su
mapping confidence: kol kodas nepasiūlytas, confidence yra null.

## Istorinių žinių sluoksnis (PHASE 6)

`parsers/historical_dbf.py` rekonstruoja tik dokumentuotą sd/dd/nd profilį;
`history.py` saugo archyvo santrauką, sąmatas, pozicijas ir peržiūros įvykius.
`history_api.py` pateikia multipart importą, filtravimą, įrodymus ir versijuotą
patvirtinimą. `mapping.py` sujungia esamą patvirtintą istoriją su istoriniais
kandidatais; vartotojo patvirtintas tikslus pasirinkimas turi pirmenybę.

React `HistoryScreen` atskirtas nuo dabartinio projekto. `EvidenceDrawer` naudojamas
ir istorijos ekrane, ir lentelės pasiūlymuose. Filtravimas ir puslapiavimas serveryje.
Materialūs resursai nekopijuojami į darbo mappingus ir nekeičia projekto kainų.
`units.py` atskiria sutampančius, perskaičiuojamus, nesuderinamus ir nežinomus vienetus.

Detali eiga ir ribos: [historical-dbf-import.md](historical-dbf-import.md).

## Privatumas ir eksploatavimas

API klausosi tik 127.0.0.1. Origin/Host tikrinimas saugo vietinį API nuo svetimų
naršyklės puslapių. Lokalus vieno naudotojo režimas, ne tinklinė daugiavartotojė paslauga.
Duomenų katalogas konfigūruojamas env; .env automatiškai nekraunamas.
Jokio AI SDK, telemetrijos, CDN ar dokumentų siuntimo. Priklausomybių diegimui reikalingas
internetas, paleistai aplikacijai – ne. Migracijos vykdomos aiškia komanda prieš paleidimą.
Kopijavimui/atsarginei kopijai sustabdyti API ir kopijuoti visą duomenų katalogą.
Logai: importo ID, parserio versija, puslapis, eilučių ir įspėjimų skaičius, klaidos kodas,
trukmė. Dokumentų tekstas ir pavadinimai į logus nerašomi.


## PHASE 7 — estimator review

`handoff.py` owns pure target-quantity validation and invalidation invariants.
`workflow.py` exposes the shared project validator and versioned explicit review
commands. GET validation is read-only; POST validation stores Project.status.
Entry marking checks central blocking issues. Existing mapping confirmation,
grid transactions, undo and document provenance remain in their original services.

React `Workflow.tsx` integrates Review Queue, source details, mapping evidence,
conversion acceptance, readiness summary and local statistics. Entry Mode V2
uses Decimal-safe clipboard values and persisted `entered_at`. Excel export keeps
source columns intact and appends separate target/review columns. No verified
automatic SISTELA import exists. See [estimator workflow](estimator-workflow.md).
