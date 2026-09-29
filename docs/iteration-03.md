# PHASE 6 rezultatas

2026-09-29. Tęsta švari commit `1944a96` būsena. Prieš pakeitimus praėjo visi
75 testai (58 backend, 14 frontend, 3 Playwright), lint, build ir migracijų patikra.
Ankstesnės veikiančios funkcijos išlaikytos.

## Įgyvendinta

- Istorinių DBF rinkinio atpažinimas ir read-only importas su aiškia koduote,
  SHA-256 prieš parsingą ir jo patikra skaitant. Atominis, idempotentiškas importas.
- Sąmatų ir istorinių pozicijų rekonstrukcija, DIRECT/DERIVED/AMBIGUOUS klasifikavimas,
  fiziniai DBF įrašų numeriai, įskaitant teisingą deleted įrašų praleidimą.
- Kandidatų CANDIDATE/CONFIRMED/REJECTED būsenos, versijų konfliktų apsauga, peržiūros
  auditas, stiprių kandidatų masinis patvirtinimas. Medžiagos – NOT_APPLICABLE.
- Istorinių kodų naudojimo agregavimas ir esamo pasiūlymų variklio išplėtimas,
  išlaikant aiškių vartotojo pasirinkimų pirmenybę. Atmesti kandidatai nesiūlomi.
- Vienetų normalizavimas ir atskiros suderinamumo / Decimal konversijos funkcijos.
  `650 m → 6.50 × 100m` yra patikrinta aiški taisyklė; automatinio pritaikymo nėra.
- Istorinių sąmatų UI: importas, santrauka, paieška, sistemos/kodo/būsenos filtrai,
  puslapiavimas, individualus ir masinis patvirtinimas, atmetimas. Įrodymų skydelis
  prieinamas ir iš dabartinės sąmatos pasiūlymo.
- Istorinės kainos laikomos tik kaip šaltinio reikšmės; dabartinės kainos, kiekiai
  ir galutinis aprašymas nuo istorinio pasiūlymo taikymo nesikeičia.

## Tikro rinkinio faktai

3 sąmatos, 104 pozicijos: **65 medžiagos ir 39 darbų kandidatai, 34 skirtingi darbų
kodai**. AS 10 darbų, GSS 13, ER 16. Nė vienas importuojant automatiškai nepatvirtintas.
Visos 104 pozicijų jungtys klasifikuotos DERIVED, rekonstrukcijos įspėjimų 0.

sd/dd 8 laukų rakto unikalumas ir kodo/kiekio sutapimas patikrinti visoms pozicijoms.
nd turi 3 unikalias POZ=3 sąmatų ir 6 POZ=4 skyrių antraštes pagal atitinkamus raktus.
Pavadinimai klasifikuoja tipus bei sistemas tik kaip dokumentuotą interpretaciją;
originalus katalogo tekstas, KODAT paskirtis ir universali SISTELA semantika nežinomi.
Detalios taisyklės: [historical-dbf-import.md](historical-dbf-import.md).

## Keisti / pridėti failai

- Domenas / migracija: `backend/sistela/models.py`,
  `backend/migrations/versions/66611011cc47_historical_knowledge.py`.
- Skaitymas ir paslaugos: `backend/sistela/parsers/dbf.py`,
  `parsers/historical_dbf.py`, `history.py`, `history_api.py`, `units.py`,
  `mapping.py`, `api.py`, `integration.py`.
- UI: `frontend/src/History.tsx`, `history.css`, `App.tsx`, `MappingPanel.tsx`, `types.ts`.
- Testai: `tests/test_history.py`, `tests/test_domain.py`,
  `frontend/src/history.test.tsx`, `frontend/e2e/history.spec.ts`,
  `frontend/e2e/workflow.spec.ts` (esamas testas tiksliau parenka savo TEST-N50 pasiūlymą,
  nes šalia jo dabar teisėtai rodomi ir istoriniai pasiūlymai).
- Dokumentai: `README.md`, `docs/architecture.md`, `docs/domain-model.md`,
  `docs/sistela-dbf-analysis.md`, `docs/historical-dbf-import.md`,
  `docs/decisions/0006-historical-knowledge.md`, `docs/progress.md`, šis dokumentas.
- Vaizdai: `docs/screenshots/historical-import.png`, `historical-evidence.png`;
  atnaujinti esamos lentelės ir Entry Mode vaizdai su nauja navigacija.

Migracija prideda tik keturias istorijos lenteles ir jų indeksus / apribojimus,
neperkuria esamų projektų ar mappingų. HistoricalLine kartu saugo vieną kandidatą;
nedubliuojame vienas-su-vienu modelių. Originalūs katalogo pavadinimai lieka tušti.

## Testai ir patikros

Pridėti **28 scenarijai**: 21 backend, 5 frontend, 2 Playwright. Iš viso:

| Patikra | Rezultatas |
|---|---:|
| Backend, su `--require-fixtures` | 79 passed |
| Frontend Vitest | 19 passed |
| Playwright Chromium | 5 passed |
| Iš viso | **103 passed**, be skip |
| Ruff / ESLint / TypeScript / Vite build | Praėjo |
| Alembic check | Skirtumų nėra |
| pip check | Priklausomybės tvarkingos |
| Visų 9 originalių failų hashai | Nepakeisti |

Bendra komanda: `powershell -ExecutionPolicy Bypass -File scripts/test.ps1 -RequireFixtures -E2E`.
Testai apima tikrą DBF importą ir nedubliavimą, hash neatitikimo atmetimą, visų
pozicijų rekonstrukciją, provenienciją, tris įrodymo klases, schemas, patvirtinimą,
atmetimą, transakcijos rollback konflikte, neaiškių įrodymų masinio patvirtinimo
draudimą, vienetų variantus/konversiją/blokavimą, agregavimą, exact/normalized/fuzzy
atitiktį ir vartotojo pasirinkimo pirmenybę. E2E apima pilną tikro archyvo eigą.
Senas tikro GSS PDF, XLSX, Entry Mode ir 500 eilučių scenarijus išliko veikiantis.

Liko tik ankstesni trečiųjų šalių įspėjimai: Starlette TestClient/httpx deprecation
ir Playwright NO_COLOR/FORCE_COLOR. Tai nėra praleisti ar nesėkmingi testai.

## UI vaizdai

[Istorijos ekranas](screenshots/historical-import.png) ·
[Įrodymų skydelis](screenshots/historical-evidence.png).

Viešinami vaizdai specialiai naudoja sintetinius demonstracinius duomenis ir TEST
kodus. Jie yra tik UI iliustracijos, ne tikrų DBF rezultatų įrodymai; realus importas
atskirai tikrinamas backend ir pilnos eigos Playwright testais.

## Žinomos ribos

- Palaikomas dokumentuotas sd/dd/nd profilis, ne visos SISTELA versijos ir archyvai.
  ZIP, memo ir indeksų importas nepalaikomas; DBF rašymo nėra.
- Sistema pagal pavadinimą ir skyriaus tipas yra interpretacijos. Kandidato
  patvirtinimas nereiškia normatyvo egzistavimo SISTELA kataloge validacijos.
- Originalus normatyvo aprašymas ir faktinė paskutinio naudojimo data nežinomi.
  `last_used_at=null`; KODAT saugomas atskirai kaip šaltinio data.
- Neaiškų kandidatą žmogus gali patvirtinti tik atskirai su aiškiu patikros pažymėjimu;
  trūkstamų kodo/vieneto/aprašymo atkūrimo redaktoriaus šiame etape nėra.
- Importuojami reikalingų įrašų duomenys, ne pilnas atkuriamas archyvas. Papildomi
  pd/td/od nekeičia pagrindinių žinių tapatybės ir nekuria resursų mappingų.
- Pakartotiniai pagrindinių failų vaizdai su pakeistais baitais importuojami atskirai.
  Agregatas nedvigubina identiškos pozicijos naudojimo, tačiau sąmatų skaičius apima
  vaizdus; archyvų versijų sujungimo / naikinimo UI dar nėra.
- Package Text išlieka EXPERIMENTAL; eksporto adapteris užblokuotas iki realaus
  SISTELA round-trip. Jokio AI, debesies ar automatinio istorinių kainų taikymo.

## Tikslus rekomenduojamas PHASE 7 darbas

Esamas darbo XLSX importas/eksportas jau veikia. Kitas žingsnis – **patikrintas
galutinės sąmatos XLSX išrašas**: eksportavimo profilis pagal sistemas ir skyrius,
Decimal pagrįstos kiekių × esamų vieneto kainų sumos, trūkstamų kainų ir nepatvirtintų
darbų peržiūra prieš eksportą bei tikro išrašo regresijos. Istorinių kainų netaikyti
automatiškai; šio XLSX nevadinti SISTELA importo formatu. Package Text gamybinį
eksportą planuoti tik atskirai gavus autentišką round-trip įrodymą.
