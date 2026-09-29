# Domeno modelis

Schema valdoma `backend/migrations/versions/231609db4375_initial_domain.py`.
ID – UUID tekstas, laikai – ISO-8601 UTC su laiko juosta. DB foreign keys įjungti.

| Esybė | Paskirtis ir papildomi sprendimai |
|---|---|
| Project | Pavadinimas, užsakovas, sistemos tipas, būsena ir auditavimo laikai. |
| SourceDocument | Projekto failas, originalus vardas, SHA-256, tipas, lokali kopija, puslapių skaičius, ištrauktas tekstas. Unikalus project_id + checksum. |
| EstimateSection | Projekto blokas, pavadinimas ir tvarka. |
| EstimateLine | Visi užduotyje išvardyti laukai, papildomai system_type ir version. |
| SistelaMapping | Normalizuotas ir tikslus šaltinio tekstas, sistemos tipas, kodas, aprašymas, naudojimo ir patvirtinimų istorija. Šiame etape lentelė dar nepildoma. |
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
Mapping kodo parinkimo ir žmogaus pasirinkimo istorijos endpointai planuojami 5 fazėje.
