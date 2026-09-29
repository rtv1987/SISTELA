# Windows platinimas — 0.1.0

## Vartotojui

1. Paleiskite **SISTELA-Assistant-Setup-0.1.0.exe**.
2. Pasirinkite **Diegti**. Darbalaukio nuoroda neprivaloma.
3. Paleiskite **SISTELA Assistant** iš meniu Pradžia. Programa atsidarys naršyklėje.
4. Sukurkite projektą ir įkelkite PDF arba Excel žiniaraštį.
5. Baigdami darbą pasirinkite **Uždaryti programą**, paskui užverkite skirtuką.

Programa skirta Windows x64, darbui interneto nereikia. Įprastam diegimui
administratoriaus teisių nereikia. Uždarius tik naršyklę programa veikia toliau;
pakartotinis paleidimas atveria jau veikiantį egzempliorių.

Duomenys saugomi **`%LOCALAPPDATA%\SISTELA Assistant`**:
`sistela.sqlite3`, `documents`, `logs`, `exports`, `backups`, `state`.
Naršyklėje atsisiunčiamą XLSX vartotojas išsaugo pasirinktoje atsisiuntimų vietoje;
`exports` rezervuotas programos valdomiems eksportams. Diegimo vieta pagal nutylėjimą:
`%LOCALAPPDATA%\Programs\SISTELA Assistant`.

Atnaujinimui paleiskite naują Setup failą. Diegiklis paprašo veikiančio proceso
saugiai sustoti, tada atnaujina programos failus. Pirmą kartą paleidus sukuriama DB;
prieš reikalingą schemos migraciją sukuriama patikrinta DB kopija `backups` aplanke.
Vien paprastas paleidimas tos pačios schemos atsarginės kopijos nekuria. Jei kopijos
ar migracijos sukurti nepavyksta, paleidimas sustoja, o DB tyliai nepakeičiama.
Automatinio grįžimo į senesnę schemą nėra. Prieš perduodant kompiuterį kitam žmogui
visą duomenų aplanką reikia tvarkyti atskirai.

**Pašalinimas išsaugo projektus, istoriją, kopijas ir atsargines kopijas.** Pakartotinai
įdiegus programa juos randa. Duomenų ištrynimo parinkties diegiklyje nėra.
**Atidaryti logų aplanką** atveria diagnostiką; logai nerašo dokumentų turinio.
Diagnostinio ZIP šioje versijoje nėra.

## Kūrėjui: pakartojamas build

Paruoštoje Windows x64 kūrėjo aplinkoje iš repo šaknies:

```powershell
.\scripts\build-windows.ps1
```

Jeigu vietinė PowerShell politika neleidžia paleisti skripto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1
```

Reikia Python 3.12 x64 (`.venv`, arba `-Python` kelias), Node/pnpm ir interneto
build priklausomybėms. Tai **tik kūrėjo** reikalavimai. Skriptas įdiegia užrakintas
runtime/build priklausomybes, vykdo `pnpm install --frozen-lockfile`, produkcinį UI
build, PyInstaller 6.22 onedir/windowed paketą ir NSIS 3.12 diegiklį. NSIS ZIP
SHA-256 tikrinamas prieš išpakavimą; galima perduoti `-Makensis` jau turimam kompiliatoriui.
Build pakartojamas komanda, tačiau dėl archyvų laiko žymų nėra bitais identiškas.
Versijos šaltinis `backend/sistela/version.py`; API, UI, Python metaduomenys ir
diegiklio pavadinimas naudoja jį. Frontend neturi atskiros produkto versijos.

Rezultatai `dist/windows/`:

- `SISTELA-Assistant-Setup-0.1.0.exe` — pagrindinis diegiklis;
- `SISTELA-Assistant-Portable-0.1.0.zip` — išpakuojamas tas pats paketas;
- `SHA256SUMS.txt` — abiejų artefaktų kontrolinės sumos;
- `SISTELA-Assistant/` — nesuspaustas paketas.

Portable reiškia paleidimą be diegimo; duomenys vis tiek laikomi AppData, ne USB ar
paketo aplanke. Neįtraukiami repo duomenys, privatūs PDF/XLSX/DBF, `.venv`, Node ar
Git. Immutable migracijos ir UI įtraukiami aiškiai. DBF tik skaitomi.

Runtime naudoja rezervuotą `127.0.0.1` socket su OS parinktu portu. Nėra reload,
Vite dev serverio ar LAN klausymo. Byte lock apsaugo vieną duomenų katalogą;
antras paleidimas tik atveria egzistuojantį egzempliorių. Valdomo serverio origin
turi sutapti su realiu portu. Runtime state nėra skirtas siųsti diagnostikai:
jame yra vietinis uždarymo tokenas.

## Automatinis tikrinimas

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1 -RequireFixtures -E2E
.venv\Scripts\python.exe scripts/smoke_windows.py
.venv\Scripts\python.exe scripts/smoke-installer.py
```

Pirmasis smoke paleidžia tikrą užšaldytą EXE izoliuotuose duomenyse ir su PATH,
kuriame yra tik System32. Tikrina frontend, vieną procesą, tikrą 21 eilutės PDF,
XLSX eksportą, istorinį DBF patvirtinimą, perkrovimą, šiukšlinę, atkūrimą, trynimą.
Antras realiai tyliai įdiegia, sukuria Start Menu nuorodą, perinstaliuoja virš
veikiančio proceso, patikrina DB ir pašalina programą. Jis atsisako veikti, jei jau
yra registruotas įdiegimas. Laikinai sukuria tikrą vartotojo registracijos įrašą ir
nuorodą; testinis uninstaller juos pašalina. Testo duomenys paliekami `tmp/`.

## Švaraus kompiuterio priėmimas su Dariumi

Šis sąrašas **dar turi būti atliktas kitame Windows kompiuteryje**. PATH izoliuotas
testas kūrėjo kompiuteryje neįrodo visų švarios OS sąlygų. Diegiklis nepasirašytas;
Windows reputacijos patikra ar organizacijos politika gali jį perspėti / blokuoti.
Nėra automatinio atnaujinimo. Tikslinė priėmimo aplinka — Windows 10/11 x64 ir
veikianti numatytoji naršyklė; kitų architektūrų netikrinome.

- [ ] Kompiuteryje nėra kūrimo įrankių; tik įprastas vartotojas.
- [ ] Patikrinta Setup SHA-256; diegimas be administratoriaus užklausos.
- [ ] Paleisti iš Start Menu: naršyklė atsiveria, terminalo lango nėra.
- [ ] Sukurti GSS projektą, importuoti tikrą PDF, matyti 21 eilutę.
- [ ] Uždaryti per programos mygtuką, paleisti vėl: projektas liko.
- [ ] Importuoti istorinius DBF, patvirtinti N50-270, perkrauti: patirtis liko.
- [ ] „Detektorių montavimas“, 28 vnt.: N50-270 pirmenybė; nėra 100M konversijos;
      dabartinė eilutė patvirtinama tik vartotojo veiksmu.
- [ ] Projektą perkelti į šiukšlinę, atkurti, vėl perkelti, galutinai ištrinti.
- [ ] Istorinė DBF patirtis ir kitas projektas vis dar pasiekiami.
- [ ] Pakartotinai įdiegti Setup: projektai ir istorija išliko.
- [ ] Vėlesnės versijos su nauja schema bandyme patikrinti `backups` kopiją.
- [ ] Pašalinti: programa / nuorodos dingsta, AppData duomenys lieka.

Schema 007 → 008 kopijavimas ir migracija tikrinami automatiniu backend testu.
Šiame kompiuteryje realus installer update tikrinamas perinstaliuojant tą pačią
0.1.0 versiją; kitos išleistos diegiklio versijos dar nėra.

## Sukurtas ir patikrintas artefaktas (2026-09-29)

`dist/windows/SISTELA-Assistant-Setup-0.1.0.exe`: **37 047 152 baitai**.
SHA-256: `93de6a5fb64ad589fb5305ef0c80eb14290f4d70669509a97262420567966e77`.

`dist/windows/SISTELA-Assistant-Portable-0.1.0.zip`: **47 417 475 baitai**.
SHA-256: `e9bdeeaa8e44521a00cc25d904a4c374bf2c62ec82bb9e3e0ca73d2e03d9dd33`.

Patikrinta Windows 11 kūrėjo kompiuteryje: abu smoke scenarijai praėjo su galutiniu
paketu; diegimas, perinstaliavimas veikiant programai, pašalinimas, DB ir svetimo
failo diegimo aplanke išsaugojimas. EXE PE antraštė: AMD64 (`0x8664`), GUI subsystem
(`2`, be konsolės). Portable archyve 449 įrašai; nėra PDF/XLSX/DBF/SQLite duomenų ar
development katalogų. Galutinė regresija: 116 backend, 46 frontend, 10 Playwright;
lint, typecheck, build, Alembic check — PASS.
