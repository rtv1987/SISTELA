# Architektūra

## Sprendimas

Viena lokali aplikacija: React/TypeScript/Vite lentelė → FastAPI → SQLAlchemy → SQLite.
Python 3.12+, pdfplumber teksto ir struktūrinių lentelių ištraukimui, openpyxl Excel,
dbfread skaitymui su Decimal skaitinių laukų parseriu, RapidFuzz būsimiems pasiūlymams.
UI planuojama 4 fazėje; šiame 0–3 etape veikia backend ir API, ne pilnas MVP.
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

## Vėlesnės fazės

4: editable grid (kokybiška React lentelės biblioteka), Tab/Enter, autosave su versija,
bulk edit, grupavimas, undo. 5: DB saugomi exact/normalized/fuzzy/history pasiūlymai,
žmogaus patvirtinimai. 6: DBF istorija tik pagal patikrintas jungtis; nepriskirti
istoriniam tekstui originalaus normatyvo autoriteto. 7: ExcelExporter darbo išrašas.
8: Vitest ir Playwright pilnos UI eigos patikra. Šiame etape UI testų imituoti negalima.

## Privatumas ir eksploatavimas

API klausosi tik 127.0.0.1. Origin/Host tikrinimas saugo vietinį API nuo svetimų
naršyklės puslapių. Lokalus vieno naudotojo režimas, ne tinklinė daugiavartotojė paslauga.
Duomenų katalogas konfigūruojamas env; .env automatiškai nekraunamas.
Jokio AI SDK, telemetrijos, CDN ar dokumentų siuntimo. Priklausomybių diegimui reikalingas
internetas, paleistai aplikacijai – ne. Migracijos vykdomos aiškia komanda prieš paleidimą.
Kopijavimui/atsarginei kopijai sustabdyti API ir kopijuoti visą duomenų katalogą.
Logai: importo ID, parserio versija, puslapis, eilučių ir įspėjimų skaičius, klaidos kodas,
trukmė. Dokumentų tekstas ir pavadinimai į logus nerašomi.
