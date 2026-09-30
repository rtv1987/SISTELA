# PHASE 6 – istorinių SISTELA DBF žinių importas

2026-09-29. Veikiantis lokalus read-only importas; ne SISTELA formato rašymo specifikacija.

## Vartotojo eiga

1. Šoninėje juostoje atverkite **Istorinės SISTELA sąmatos**.
2. Pasirinkite vieno rinkinio `sd*.dbf`, `dd*.dbf`, `nd*.dbf`; galima kartu pateikti
   `pd`, `td`, `od`. Failų sufiksai turi sutapti. Viso įkėlimo limitas 25 MB.
3. Aiškiai pasirinkite koduotę. Pateiktam rinkiniui reikia `cp1257`, nepaisant LDID.
4. Peržiūrėkite importo santrauką, filtruokite pagal sistemą, kodą, būseną ar aprašymą.
5. Atverkite **Įrodymai**: objektas, sąmata, skyrius, istorinis tekstas, kiekis ir
   vienetas, DBF failas / fizinis įrašo numeris. Techninėje dalyje saugomi hashai,
   jungties laukai ir originalūs įrašai. Katalogo originalas automatiškai neatkuriamas.
6. Pasirinkę **Peržiūrėti**, patikrinkite sistemą ir patvirtinkite kandidatą arba jį
   atmeskite. Masinis patvirtinimas taikomas tik stipriems neambivalentiškiems darbams
   su žinomais sistema, aprašymu, kodu ir vienetu. Neaiškus kandidatas patvirtinamas
   tik individualiai, aiškiai pažymėjus, kad jo kodas ir vienetas patikrinti savarankiškai.
7. Dabartinio projekto darbo eilutėje matysite istorinius pasiūlymus ir jų įrodymus.
   Pritaikymas palieka `suggested`; dabartinės eilutės normatyvą reikia patvirtinti.
   Kainos, kiekis ir galutinis pavadinimas nuo pasiūlymo taikymo nesikeičia.

## FACT: pateikto rinkinio rezultatas

Prieš analizę visų originalų hashai sutapo su `samples/manifest.json`.

| Sąmatos pavadinimas iš nd | Sistema (INFERENCE) | Medžiagos | Darbų kandidatai |
|---|---|---:|---:|
| Apsauginė signalizacija | AS | 20 | 10 |
| Gaisro aptikimo ir signalizavimo sistema | GSS | 20 | 13 |
| Elektroniniai ryšiai | ER | 25 | 16 |
| Iš viso | | 65 | 39 |

104 pozicijos, 3 sąmatos, 34 skirtingi darbų kodai. Visos 104 sd/dd pozicijų
jungtys vienareikšmės; 39 darbai gauna `CANDIDATE`, medžiagos `NOT_APPLICABLE`.
Importas nesukuria nė vieno `CONFIRMED` pasirinkimo. Rekonstrukcijos įspėjimų 0;
tai nereiškia patvirtinto SISTELA katalogo ar teisingų kainodaros taisyklių.

## FACT, DERIVED ir UNKNOWN

**FACT:** `dd GRUP=10` tame pačiame įraše turi `IKAINIS`, `PAVADIN`, `MATO_PAV`,
`KIEKIS`. `KODAS=S` čia nenaudojamas kaip normatyvo kodas. `sd` neturi aprašymo.
Raktas `KOMPLEKSAS, OBJEKTAS, RANGOVAS, SAMATA, SKYRIUS, SUSDARB1, SAM_EILUTE,
DET_EILUTE` šiame rinkinyje sujungia 104 unikalias sd ir dd antraščių pozicijas;
visur sutampa `IKAINIS` ir `KIEKIS`.

**FACT:** nd turi 3 unikalias `POZ=3, SKYRIUS=null` sąmatų antraštes pagal pirmus
4 rakto laukus ir 6 unikalias `POZ=4` skyrių antraštes pridėjus SKYRIUS. Kiekviena
importuojama pozicija turi po vieną tokią sąmatą ir skyrių. Objektas siejamas pagal
KOMPLEKSAS/OBJEKTAS su `POZ=2, SAMATA=null`. Šios kardinalumo taisyklės tikrinamos
kiekvieno importo metu; tai nėra universali SISTELA foreign key deklaracija.

**DERIVED:** sd/dd vienareikšmė jungtis leidžia istorinei pozicijai priskirti tekstą,
kodą ir vienetą. Įrodymo klasės:

- `DIRECT`: nėra sd tėvinio įrašo, bet dd antraštė tiesiogiai turi aprašymą ir kodą,
  o sąmatos / skyriaus kontekstas vienareikšmis. Tai tik kandidatas.
- `DERIVED`: vienas sd tėvas ir viena dd antraštė, sutampa raktas, kodas ir kiekis;
  sąmatos ir skyriaus kontekstas vienareikšmis.
- `AMBIGUOUS`: daug tėvų / antraščių, kodo ar kiekio neatitikimas, neaiški sąmata,
  skyrius, tipas arba trūksta reikšmių. Pasiūlymo taikymas blokuojamas iki atskiro
  žmogaus patvirtinimo, masinis patvirtinimas draudžiamas.

**INFERENCE:** tipas pagal skyriaus tekstą „Darbai“ / „Medžiagos“; sistema pagal
aiškų sąmatos pavadinimo alias. Sistema parodoma ir redaguojama patvirtinant kandidatą.
Neatpažintas pavadinimas nesukuria išgalvotos sistemos.

**UNKNOWN:** originalus normatyvo katalogo aprašymas; faktinė paskutinio naudojimo
data; universali POZ/GRUP/MATOVNT semantika; pd/td/od kainodaros taisyklės. `KODAT`
saugomas kaip `source_date`, API `last_used_at=null`; importo laikas nėra panaudojimo
laikas. `historical_price` – neinterpretuotas dd antraštės `KAINA`, o ne įrodytas
normatyvo vieneto įkainis. Įrodymuose aiškiai nurodomas jo šaltinis ir nepatvirtinta paskirtis.

## Saugojimas ir idempotentiškumas

Migracija `66611011cc47_historical_knowledge.py` prideda keturias lenteles:
`historical_imports`, `historical_estimates`, `historical_lines`, `historical_reviews`.
HistoricalLine saugo ir poziciją, ir vieną jos kandidatą; atskiros dubliuojančios
HistoricalMappingCandidate lentelės nėra. Peržiūros įvykiai saugomi atskirai.

SHA-256 skaičiuojamas kiekvienam įkeltam failui prieš parsingą ir tikrinamas skaitant.
Importo tapatybė yra surūšiuotų **sd/dd/nd turinio hashų** digest. Failų pervadinimas,
įkėlimo tvarka ar papildomi pd/td/od failai nekeičia žinių tapatybės. Pakartojimas
grąžina esamą importą su `duplicate=true`. Kita koduotė tam pačiam turiniui grąžina
409, o ne tyliai pakeičia jau išsaugotą tekstą. Pakeistas pagrindinio failo turinys
yra atskiras archyvo momentinis vaizdas.

HTTP priima failų baitus, ne serverio katalogo kelią. Skaitymui naudojamos laikinos
nepakeistų įkėlimų kopijos; originalų keliai neatveriami rašymui. DB saugomi failų
vardai, hashai ir reikalingų įrašų duomenys, ne pilna atkuriama SISTELA archyvo kopija.
Paslauga vienoje transakcijoje išsaugo importą, sąmatas ir eilutes. Schema/koduotė/hash
neatitikimas grąžina klaidą be dalinių istorijos įrašų. Loguose tik ID ir skaitikliai.

Peržiūra tikrina eilutės `version`, visą pasirinktą rinkinį patvirtina arba atmeta
atomiškai. Konfliktas – 409. Ankstesni pasirinkimai išlieka audite. Istorijos atmetimas
neanuliuoja atskiro žmogaus patvirtinimo dabartiniame projekte.

## Agregavimas ir prioritetai

Vienos sistemos panašūs aprašymai grupuojami pagal kodą ir normalizuotą vienetą.
Rodomi naudojimai, atskiri objektai, sąmatos, skirtingi aprašymai, patvirtinimų skaičius,
įrodymų kokybė ir šaltiniai. Naudojimas – unikali išorinė pozicija + aprašymas + kodas
+ vienetas; identiška pozicija kitame momentiniame vaizde skaičiaus nedidina. Objektas
identifikuojamas KOMPLEKSAS/OBJEKTAS pora. Sąmatų skaičius apima importuotus vaizdus.
Atmesti kandidatai neįtraukiami. Dažnis nėra normatyvo teisingumo įrodymas.

Taikomi pasiūlymai rikiuojami prieš blokuotus. Toliau: vartotojo patvirtinti
atitikmenys, žmogaus patvirtinta istorinė patirtis, nepatvirtinti istoriniai kandidatai.
Patvirtinta istorija toje pačioje sistemoje ir su suderinamu vienetu įtraukiama net
kai skiriasi aprašymų formuluotės; 0.45 tekstinio panašumo slenkstis lieka
nepatvirtintiems kandidatams. m/100m pora gali būti siūloma tik su atskiru aiškiu
konversijos patvirtinimu. Nesuderinami patvirtintos istorijos vienetai neįtraukiami.
Teksto įvertis nepadidinamas dėl patvirtinimo; UI atskirai rodo „Patvirtinta istorinė
patirtis“ ir įrodymus. Tai kandidatų sąrašas, ne semantinio tapatumo įrodymas.
Dabartinę eilutę būtina atskirai pritaikyti ir patvirtinti. Istorinės būsenos jau
saugomos HistoricalLine / HistoricalReview; jų nereikia dubliuoti į SistelaMapping.
Išlaikyta ankstesnio vartotojo pataisymo naujumo pirmenybė savo grupėje.
Įvertis – euristika, ne tikimybė.

## Vienetai

`VNT/vnt./vnt`, `M/m`, `KOMPL/kompl.`, `100M/100m` normalizuojami. Grąžinama
`IDENTICAL`, `CONVERTIBLE`, `INCOMPATIBLE` arba `UNKNOWN`.

Aiškios taisyklės: m → 100m daugiklis 0.01, 100m → m daugiklis 100. Decimal
`650 m → 6.50 × 100m`. `POST /units/convert` tik apskaičiuoja peržiūros rezultatą
(`applied=false`), jokios eilutės nekeičia. Pasiūlymo taikymas leidžiamas tik sutampant
vienetams; vartotojas atskirai pakeičia kiekį ir vienetą lentelėje. `vnt.` → `m`
neturi konversijos, tušti vienetai nežinomi. Istorinės kainos niekada nepritaikomos.

## API ir ribos

- GET/POST `/history/imports` – sąrašas / multipart failų importas.
- GET `/history/lines` – import_id, search, system, code, status, limit, offset.
- GET `/history/lines/{id}/evidence` – visa kilmė ir peržiūros istorija.
- POST `/history/review` – items[{id,version,system_type}], status, acknowledge_ambiguity.
- Esami `/projects/{id}/lines/{id}/suggestions` ir `/mapping/apply` išplėsti;
  istoriniai pasiūlymai turi `origin=historical` ir `evidence_ids`.

Palaikomas dokumentuotas sd/dd/nd profilis, iki 10000 sd ir 100000 dd įrašų.
ZIP, indeksų ar memo failų importas neįgyvendintas; jų reikalaujančios DBF versijos
atmetamos. pd/td/od perskaitomi ir tikrinami, tačiau jų išteklių eilutės nekuria
darbų kandidatų. Patvirtinimas nėra normatyvo egzistavimo SISTELA kataloge validacija.
Package Text išlieka EXPERIMENTAL ir jo eksportas blokuotas. PHASE 9 leidžia tik
atskirą eksperimentinį DBF klonavimo rašytoją; istorinis importas lieka read-only.
Žr. [DBF round-trip](sistela-dbf-roundtrip.md).

Patikros rezultatai ir failai: [iteration-03.md](iteration-03.md).
