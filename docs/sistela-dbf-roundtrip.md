# DBF round-trip: pirmas realus bandymas

Būsena: **EXPERIMENTAL**. Originalus archyvas priimtas SISTELA pagal kliento
patvirtinimą. Mūsų sugeneruotų archyvų importas SISTELA dar nebandytas.

## Sugeneruoti paketai

Kūrėjo darbo vietoje: `data/exports/TEST_A_CLONE` ir
`data/exports/TEST_B_ONE_CHANGE`. Kiekviename yra šeši originaliai pavadinti DBF,
`manifest.json` su SHA-256 ir `analysis.json` su visų laukų klasifikacija.
Paketai privatūs, ignoruojami Git; jie neįtraukiami į Windows diegiklį.
Perdavimui sukurti `data/exports/TEST_A_CLONE.zip` ir `TEST_B_ONE_CHANGE.zip`.

**TEST_A:** parse → normalizuoti C/Decimal/date įrašai → mūsų serializeris →
pakartotinis nuskaitymas. Tai nėra failų kopijavimo funkcija. Rezultatas **SAME**:
232 laukų schema, visi 697 fiziniai įrašai, 104 sd/dd jungtys ir trys sąmatos
sutampa. Šiame konkrečiame rinkinyje sutapo net visų šešių failų SHA-256; to nereikalaujame
kaip bendros sąlygos, jei ateityje pagrįstai pasikeis header metaduomenys.

**TEST_B:** pakeistas tik `dd25-04-14.dbf`, fizinis įrašas **174**, laukas **PAVADIN**.
Prie esamo teksto pridėta **` [TEST_B]`**. Kontekstas: SAMATA=2, SKYRIUS=2,
SAM_EILUTE=2, DET_EILUTE=2, IKAINIS=N50-270, GRUP=10, KIEKIS=115.000000.
Tai istorinio GSS darbų skyriaus eilutė, ne dabartinio projekto 28 vnt. eilutė.
Tikslus senas/naujas tekstas užrašytas TEST_B manifest.json; loguose jo nėra.
Visi skaičiai, kainos, sumos, koeficientai, identifikatoriai ir kiti penki failai
nepakeisti. Normalizuotas palyginimas grąžina **DIFFERENT** ir tik vieną priežastį:
`dd record 174 field PAVADIN: value differs`. Abiejų rinkinių jungtys praeina.

**Kiekis TEST_B nekeičiamas.** Kiekio mutacija sąmoningai grąžina BLOCKER:
neįrodytos dd išteklių, pd ir td sumų priklausomybės. Šis testas nepatvirtins kiekio
perskaičiavimo ar naujo projekto eksporto. Jam reikės atskiro paskesnio bandymo:
SISTELA programoje pakeisti vieną kiekį ir eksportuoti prieš/po archyvus palyginimui.

## Instrukcija Dariui

1. Išpakuok TEST_A_CLONE.zip. Pasirink atskirą bandymo kontekstą SISTELA; nenaudok
   aktyvios darbinės sąmatos. Klonas turi originalius identifikatorius. Jei siūloma
   perrašyti darbinę sąmatą, atšauk ir pasirink saugią bandymo vietą.
2. Naudok **tą pačią archyvo importavimo funkciją**, kuria jau sėkmingai perkėlei
   originalius DBF tarp kompiuterių. Pasirink TEST_A šešis DBF / jų aplanką taip pat,
   kaip rinkaisi originalą. JSON ir šios instrukcijos SISTELA neimportuoja.
3. Atverk atkurtas sąmatas. Tikimasi tų pačių trijų sąmatų, pavadinimų, eilučių ir
   sumų kaip importavus originalą: AS 30 pozicijų (20 medžiagų / 10 darbų), GSS 33
   (20 / 13), ER 41 (25 / 16). Palygink skyrių, sąmatų, procentų ir galutines sumas
   su originalu. N50-270 GSS darbo kiekis turi būti 115, ne 28.
4. Užrašyk rezultatą, SISTELA versiją ir importo metu pasirinktus nustatymus.
5. Atskirame tokiame pat saugiame bandymo kontekste importuok išpakuotą TEST_B.
   Nemaišyk failų iš A, B ir originalo; jų vardai sutampa sąmoningai.
6. GSS → Darbai → antra pozicija N50-270: aprašymo gale turi būti `[TEST_B]`.
   Kiekis turi likti 115, o visos kainos, procentai ir sumos turi sutapti su TEST_A.
7. Pranešk atskirai apie A ir B: ar importuota, ar atsiveria, ar tekstas išliko po
   uždarymo/pakartotinio atvėrimo. Perduok tikslų klaidos tekstą / lango vaizdą ir
   bet kokį netikėtą perskaičiavimą, įskaitant skirtumus nuo originalaus importo.
8. Jei abu pavyko, paruošk kontroliuojamą **prieš/po** archyvų porą pačioje SISTELA:
   bandomos N50-270 eilutės kiekį 115 pakeisk į 116, išsaugok ir vėl eksportuok
   visus šešis DBF. Užrašyk, ar programa pati perskaičiavo ir kokius veiksmus atlikai.
   Tai bus įrodymas tolimesnei kiekio ir PROJECT_EXPORT realizacijai, o ne dabartinio
   rašytojo leidimas spėti formules.

Nė vienas paketas nenukopijuojamas į SISTELA katalogą automatiškai. Tik Darius
naudoja SISTELA importavimo funkciją. Automatinis statuso SUPPORTED perjungimas
neįdiegtas. Net A/B teksto bandymo sėkmė neįrodo finansinių ar ID generavimo taisyklių.

## Kūrėjo komandos

```powershell
.venv\Scripts\python.exe scripts/dbf_roundtrip.py . --destination TEST_A_CLONE
.venv\Scripts\python.exe scripts/compare_dbf_archives.py . data/exports/TEST_A_CLONE
.venv\Scripts\python.exe scripts/compare_dbf_archives.py . data/exports/TEST_B_ONE_CHANGE
```

Palyginimas grąžina exit 0 SAME; exit 1 DIFFERENT / netinkami duomenys. TEST_B exit 1
yra laukiama. CLI mutacijai `--record 174 --description "<visas naujas tekstas>"`;
`--quantity` visada blokuojamas. Esamo paskirties aplanko perrašyti negalima; naujam
bandymui naudok naują aplanko vardą. Vartotojo katalogo kelias nepriimamas.

UI: **Paruošta SISTELA → Eksperimentinis DBF eksportas**. Pasirenkami šeši failai,
gaunamas bandomasis klonas ZIP. Projektas nekeičiamas ir neeksportuojamas.
**Tikrinti projekto DBF kliūtis** parodo review klaidas bei neįrodytas formato taisykles.
`GET /projects/{id}/dbf/plan` saugo atskiras source/target reikšmes ir aprašymų
sąvokas, tikrina lauko pločius, patvirtinimus ir pateikia deterministinius ID
pasiūlymus. `POST /projects/{id}/export/dbf` grąžina 409 su kliūtimis, nerašo failų.

Realaus priėmimo įrašas: **PENDING** (A), **PENDING** (B). Negalima šių būsenų pakeisti
vien dėl automatinių parserio/serializerio testų sėkmės.
