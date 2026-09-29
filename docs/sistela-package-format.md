# SISTELA Package Text: EXPERIMENTAL tyrimo būsena

2026-09-28. Tai tyrimo dokumentas, ne SISTELA formato specifikacija.

## FACT

- Užduotyje minimas „Informacija pakete“ / Package Text mechanizmas.
- Repo pateikti PDF, XLSX ir DBF; autentiško paketinio teksto pavyzdžio nėra.
- DBF laukų struktūra neįrodo tekstinio paketo gramatikos.
- Vieša paieška ir [SISTELA svetainės](https://sistela.lt/) patikra šiame etape
  nepateikė patikrinamos paketinio teksto specifikacijos. Tai neįrodo, kad jos nėra.
- Programos eksportavimo adapteris blokuotas ir neturi HTTP maršruto ar UI mygtuko.

## UNKNOWN

Palaikomos SISTELA versijos, licencijos/moduliai, failo plėtinys, koduotė,
skirtukai, laukų tvarka, sekcijų žymos, escaping, kainų/koeficientų taisyklės,
normatyvinių vienetų konversijos, naujo ir esamo įrašo semantika, klaidų ir
dalinio importo elgesys. Negeneruoti tariamo formato iš kodo ir kiekio porų.

## Įgyvendintas read-only parseris

`PackageTextParser` grąžina SHA-256, koduotę, baitų skaičių, visą išdekoduotą tekstą,
numeruotas eilutes su jų pabaigomis, literal tab langelius ir kodo formos kandidatus.
Jis neišmeta nežinomų eilučių, nevykdo komandų, nesukuria EstimateLine ar mappingų.
`grammar_status=UNKNOWN` visada. Tab išskaidymas – teksto faktas, ne deklaruotas
paketo skirtukas. `N...-...` atitikmuo – leksinis požymis, ne kodo validacija.
UTF-8 numatytoji koduotė; cp1257/cp1252/UTF-16 tik aiškiai pasirinkus. Strict decoding,
5 MB limitas. Originalūs baitai nekeičiami; BOM gali būti pašalintas dekoduojant,
todėl teksto rezultatas nėra byte-for-byte serializeris.

```powershell
.\.venv\Scripts\python.exe scripts/analyze_package.py C:\Samples\package.txt `
  --encoding cp1257 --output tmp\package-analysis.json
```

Rezultato JSON turi konfidencialų tekstą, laikomas lokaliai. Į stdout rašomi tik
metaduomenys. Esamas išvesties failas neperrašomas. Unit testų tekstas sintetinis ir
nevadinamas SISTELA fixture. CLI nenaudojamas automatiškai gamybiniame importo kelyje.

## INFERENCE ir patvirtinimo planas

Tekstinis paketas galėtų tapti adapteriu tik gavus tiekėjo specifikaciją arba
kontroliuojamai eksportuotus tikrus pavyzdžius. Reikia atskirų vienos medžiagos,
vieno darbo, pakeisto pavadinimo, dešimtainio kiekio ir `100m` normatyvo pavyzdžių.
Fiksuoti programos versiją, veiksmą ir SHA-256, palyginti vieno lauko pakeitimus.
Tuomet testinėje SISTELA sąmatoje atlikti import/export round-trip su vartotojo
patikrintais kodais, kiekiais, vienetais, pavadinimais ir išteklių skaičiavimais.
Tik po šio įrodymo galima pakeisti capability būseną ir kurti writer implementaciją.

Šis nežinojimas nestabdo rankinio Entry Mode ar mūsų darbo XLSX formato.
