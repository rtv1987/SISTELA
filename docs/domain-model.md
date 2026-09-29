# Domeno modelis

Schema valdoma Alembic migracijomis `backend/migrations/versions/`; naujausia – `66611011cc47_historical_knowledge.py`.
ID – UUID tekstas, laikai – ISO-8601 UTC su laiko juosta. DB foreign keys įjungti.

| Esybė | Paskirtis ir papildomi sprendimai |
|---|---|
| Project | Pavadinimas, užsakovas, sistemos tipas, būsena ir auditavimo laikai. |
| SourceDocument | Projekto failas, originalus vardas, SHA-256, tipas, lokali kopija, puslapių skaičius, ištrauktas tekstas. Unikalus project_id + checksum. |
| EstimateSection | Projekto blokas, pavadinimas ir tvarka. |
| EstimateLine | Visi užduotyje išvardyti laukai, papildomai system_type ir version. |
| SistelaMapping | Normalizuotas ir tikslus šaltinio tekstas, sistemos tipas, kodas, aprašymas, naudojimo ir patvirtinimų istorija. Pildoma tik aiškiai patvirtinus dabartinio projekto normatyvą. Unikalumas apima sistemą, normalizuotą tekstą, vienetą ir kodą. |
| ImportRun | Parserio versija, būsena, trukmė, klaida, puslapiai, eilučių skaičius ir struktūriniai įspėjimai. |
| Requirement | Reikalavimas, projekto ID, pasirinktinė eilutės ir dokumento nuoroda, puslapis, tekstas, tipas. Automatinio produkto parinkimo nėra. |

`EstimateLine` skiria keturis nepriklausomus laukus:

- project_description: projekto žiniaraščio tekstas.
- sistela_code: normatyvinio recepto identifikatorius.
- sistela_original_description: tik žinomas originalaus katalogo aprašymas.
- output_description: vartotojo pasirinktas galutinis tekstas.

Importas pradžioje nukopijuoja projekto tekstą į output_description, bet vėlesni
pakeitimai neprivalo sutapti. Kodo pakeitimas DB negali automatiškai perrašyti tekstų.
Istorinis pervadintas aprašymas nėra originalus normatyvo aprašymas.

Kiekiai ir kainos – Python Decimal / SQLite TEXT. API priima dešimtaines eilutes,
iki 24 skaitmenų ir 6 dešimtainių vietų, neigiamus ir nebaigtinius skaičius atmeta.
Nėra numanomo perskaičiavimo tarp `m` ir `100m`, tarp `vnt.` ir `kompl.`.
Tuščia kaina yra null, ne nulis. Confidence null reiškia „pasiūlymo nėra“.

Sudėtiniai foreign keys užtikrina, kad eilutės skyrius ir šaltinis priklausytų tam
pačiam projektui; analogiškai ImportRun ir Requirement. Originali pozicija nėra
unikali: GSS medžiagų ir darbų numeracija prasideda nuo 1 atskirai.
Importo eilutės turi `mapping_status=unmapped`, importas `needs_review`.
`ROW_REJECTED` įspėjimai nurodo puslapį ir lentelės eilutę; šaltinis lieka pasiekiamas lokaliai.

Eilutės PUT naudoja optimistinę `version` patikrą SQL UPDATE sąlygoje.
Pasenusi versija grąžina 409. Šaltinio/ID/audito laukai per PUT nekeičiami.
Mapping kodo parinkimas, žmogaus patvirtinimai ir jų istorijos endpointai veikia.


## Istorinės esybės

| Esybė | Paskirtis |
|---|---|
| HistoricalImport | Unikalus pagrindinių failų source_hash, failų vardai/hashai/dydžiai, koduotė, importo laikas, būsena, parserio versija ir įspėjimai. |
| HistoricalEstimate | Importo FK, išoriniai kompleksas/objektas/rangovas/sąmata raktai JSON, objektas, sąmatos vardas, numanoma sistema, jos įrodymo tipas, source_date ir nd kilmė. |
| HistoricalLine | Sąmatos FK, išorinė pozicija, tipas, istorinis ir normalizuotas aprašymas, kodas, nežinomas katalogo originalas (tuščias), vienetas, Decimal kiekis, historical_price, skyrius, sistema, kokybė, įrodymų JSON, kandidato statusas ir version. |
| HistoricalReview | Istorinės eilutės FK, buvusi/nauja būsena, patvirtinta sistema, neaiškumo pripažinimas ir peržiūros laikas. |

HistoricalLine kartu atlieka HistoricalMappingCandidate vaidmenį; medžiagos turi
NOT_APPLICABLE. Darbų būsenos CANDIDATE/CONFIRMED/REJECTED ir įrodymo klasės
DIRECT/DERIVED/AMBIGUOUS apribotos CHECK sąlygomis. Automatinio CONFIRMED nėra.
Istorinės ir einamojo projekto peržiūros nesuplakamos; istorijos atmetimas nepanaikina
vėlesnio savarankiško žmogaus sprendimo projekte.

HistoricalEstimate.source_date saugo tik nd KODAT, ne paskutinio panaudojimo faktą.
HistoricalLine.historical_price saugo raw dd GRUP=10 KAINA. Abiejų semantika ribota;
šaltinio įrašas ir importo laikas visada pasiekiami. Originalus istorinis tekstas
niekada automatiškai neįrašomas į sistela_original_description.


## PHASE 7 review state

Migration `007_estimator_review` adds `EstimateLine.review_data` (JSON) and expands
the mapping-state CHECK with `rejected` and `needs_review`, preserving existing
rows, source foreign keys and the other row CHECK constraints. Domain models do
not participate in migration execution.

The versioned review snapshot contains the explicitly accepted conversion
(source/target decimal strings, units, rule, user confirmation and timestamp),
selected suggestion evidence, rejected suggestion identifiers, manual-selection
flag, confirmation category, first-reviewed suggestion availability, price status
and duplicate-pair acknowledgments. No current-project quantity is replaced.
Source edits invalidate a conversion; duplication clears review approvals.
Price edits clear price approval. Mapping confirmations still use the existing
MappingConfirmation audit and SistelaMapping history.

Project.status uses IMPORTED, NEEDS_REVIEW, MAPPING_IN_PROGRESS,
READY_FOR_SISTELA and HANDED_OFF during review. Existing newly created draft
projects remain compatible; an empty project cannot pass validation. HANDED_OFF
records user-marked work entry, not a receipt from SISTELA. Local metrics aggregate
current rows and stored decisions; they are not cumulative usage telemetry.
