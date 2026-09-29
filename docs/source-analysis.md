# Šaltinių analizė

Analizuota 2026-09-28. Faktai gauti iš failų, ne iš užduoties pavyzdinių eilučių.
Kontrolinės sumos ir dydžiai: `samples/manifest.json`. Originalai palikti repo šaknyje.

## FACT: GSS PDF

`2024-10-XX-TDP-GSS.pdf`, 17 puslapių, tekstas ištraukiamas visuose puslapiuose.
1 p. antraštinis; 2 p. projekto sudėties žiniaraštis; 3 p. bylos sudėtis;
4–7 p. aiškinamasis raštas; 8–13 p. techninės specifikacijos;
14 p. sąnaudų žiniaraštis; 15 p. principinė schema; 16 p. elementų išdėstymo planas;
17 p. „PRIEDAI“. Bylos turinyje nurodyta 18 puslapių, tačiau gautame PDF yra 17.
Tai šaltinio neatitikimas; trūkstamo priedo turinys neatkuriamas.

14 p. vizualiai patikrintas. Šešios loginės kolonos:
pozicija, pavadinimas ir techninės charakteristikos, žymuo, mato vnt., kiekis, pastabos.
11 medžiagų eilučių, po „MONTAVIMO DARBAI“ – 10 darbų eilučių.
Medžiagų blokas neturi atskiros „MEDŽIAGOS“ antraštės.
Pozicijos darbų bloke prasideda iš naujo, todėl pozicija nėra unikalus ID.

`pdfplumber` linijų lentelės ištraukimas grąžina 14 fizinių kolonų dėl apačioje
esančio dokumento štampo. Loginės kolonos nustatomos pagal antraštes, ne indeksų
konstantas. Kelių eilučių langeliai išlaiko visą pavadinimą. Vienoje darbo eilutėje
tekstas išsklaidytas: `T S 2 . 2`, `v n t .`; žali duomenys turi išlikti.
Antraštė taip pat minima turinyje ir štampe: vien raktažodžio puslapyje nepakanka.

Svarbūs tikro failo skirtumai nuo užduoties santraukos:
- 50 m eilutė vadinasi „Gaisrinės signalizacijos kabelis 3x1,5 mm2“, žymuo HDGS.
- 9 vnt. medžiaga – „Ranka valdomas pavojaus signalizavimo įtaisas“, žymuo FP3.
- Dūmų detektoriaus komplekto vienetas `kompl.`, montavimo – `vnt.`.

## FACT: XLSX

`pvz.xlsx`: Sheet1 – 530 × 11 naudojamo diapazono matmenys; Sheet2 ir Sheet3 tušti.
Tai suformatuotas istorinės lokalios sąmatos išrašas, ne plokščia importo lentelė.
Pirmos lentelės antraštės 12–13 eilutėse; A pozicija, B kodas, C aprašymas,
D vienetas, E kiekis, F darbo sąnaudos, G vieneto kaina, H–K kainos komponentai.
14 eilutėje „Medžiagos“, duomenys nuo 15 eilutės; 36 eilutėje „Darbai“.
Iš viso 30 pozicijų su skaitiniu kiekiu (20 medžiagų, 10 darbų), toliau sumos.
Sheet1 turi 37 sujungtus diapazonus ir neturi formulių; kainos yra išsaugotos reikšmės.
B38 `N50-210`, C38 „Kabelio tiesimas“, D38 `100m`, E38 `49.14`.
Pavadinimai yra istorinio pasiūlymo tekstas; originalus normatyvo pavadinimas neįrodytas.
Formulių, eilučių ir sujungimų inventorius išsaugomas lokaliai analizės įrankiu.

## FACT: papildomas PDF

`Efektyvus inžinerinis darbas su DI - Google Gemini.pdf` – 31 p. pokalbio išrašas.
Pradinio teksto ištraukimo metu matomi dubliuoti persidengiantys simboliai.
Tai kontekstinis dokumentas, ne SISTELA formato specifikacija ir ne GSS regresinis fixture.
Jame esančios rekomendacijos nelaikomos patvirtintu SISTELA elgesiu.

## Rizikos ir sprendimai

- Medžiagų klasifikavimas be antraštės yra INFERENCE, todėl importas palieka peržiūros būseną.
- Table extraction remiasi struktūra ir antraštėmis; kitoks išdėstymas gali būti nepalaikomas.
  Neperskaitytas dokumentas turi grąžinti aiškią klaidą, ne tuščią sėkmingą importą.
- Skenuoti PDF: OCR_REQUIRED, be automatinio OCR ar siuntimo į internetą.
- Techniniai modeliai iš šaltinio nėra automatinė produkto parinkimo rekomendacija.
- `100m` ir normatyviniai kiekiai negali būti sujungiami su projekto `m` be konversijos.
- DBF koduotės žyma klaidinga šiam rinkiniui; žr. atskirą DBF analizę.

## Atkūrimas

`python scripts/inspect_sources.py` perskaito originalus ir rašo tik į
`tmp/source-inspection/`. Šis katalogas neįtraukiamas į Git ir nėra programos logas.
Pilnas tekstas ir eilučių išrašai lieka tik lokaliai. SHA-256 prieš/po skaitymo
regresiniuose testuose saugo originalų nekeičiamumą.
