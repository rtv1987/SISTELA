# SISTELA DBF analizė

Atlikta 2026-09-28. FACT = perskaityti baitai ir įrašų patikra;
INFERENCE = siūloma domeno reikšmė; UNKNOWN = nepatvirtinta.

## FACT: bendras formatas

Visi pateikti failai: version 0x30 (Visual FoxPro), LDID=3.
dbfread pagal žymą parenka cp1252. Šiam rinkiniui aiškiai naudota cp1257.
cp1257 tekstas „Įeigos kontrolinis įrenginys“ sutampa su pvz.xlsx C15.
Visi įrašai dekoduoti strict režimu; N/F skaičiai skaitomi kaip Decimal.
Blank skaitinis laukas lieka null. Visi šaltiniai tik skaityti.

| Failas | Laukai | Deklaruota | Aktyvių | Ištrintų |
|---|---:|---:|---:|---:|
| dd25-04-14.dbf | 50 | 391 | 391 | 0 |
| nd25-04-14.dbf | 55 | 11 | 11 | 0 |
| od25-04-14.dbf | 16 | 0 | 0 | 0 |
| pd25-04-14.dbf | 24 | 143 | 143 | 0 |
| sd25-04-14.dbf | 45 | 104 | 104 | 0 |
| td25-04-14.dbf | 42 | 48 | 48 | 0 |

## FACT: dd25-04-14.dbf

SHA-256: `30c0ea73fa3839b15d3239116b413f62d45e2b8be11537e601965092a0421a96`

| Laukas | Tipas | Baitai | Dešimtainės vietos |
|---|---|---:|---:|
| KOMPLEKSAS | C | 10 | 0 |
| OBJEKTAS | N | 7 | 0 |
| RANGOVAS | N | 4 | 0 |
| SAMATA | N | 3 | 0 |
| SKYRIUS | N | 4 | 0 |
| SUSDARB1 | N | 3 | 0 |
| SAM_EILUTE | N | 4 | 0 |
| DET_EILUTE | N | 4 | 0 |
| GRUP | N | 2 | 0 |
| IKAINIS | C | 18 | 0 |
| K1 | N | 5 | 2 |
| K2 | N | 5 | 2 |
| K3 | N | 6 | 3 |
| K4 | N | 7 | 3 |
| KODAS | C | 18 | 0 |
| MATO_PAV | C | 20 | 0 |
| KIEKIS | N | 13 | 6 |
| NORMA | N | 11 | 6 |
| KAINA | N | 12 | 4 |
| VERTE | N | 9 | 2 |
| PAVADIN | C | 240 | 0 |
| NGR4 | N | 2 | 0 |
| KODSUS | C | 10 | 0 |
| MVNTSUS | N | 3 | 0 |
| KOEFSUS | N | 10 | 5 |
| K5 | N | 9 | 5 |
| KAINBEK5 | N | 12 | 4 |
| VNTKAIN | N | 12 | 4 |
| DETEIL1 | N | 4 | 0 |
| SUS1 | C | 8 | 0 |
| MVNTS1 | N | 3 | 0 |
| KOEF1 | N | 11 | 5 |
| FIZKIE1 | N | 13 | 6 |
| SUS2 | C | 8 | 0 |
| KOEF2 | N | 11 | 5 |
| FIZKIE2 | N | 13 | 6 |
| POZYS | N | 1 | 0 |
| POSU | N | 1 | 0 |
| VYKDYTOJAS | N | 4 | 0 |
| SDET_EIL | N | 4 | 0 |
| SDET_EI1 | N | 4 | 0 |
| XSAMATA | C | 8 | 0 |
| XSKYRIUS | C | 8 | 0 |
| K6 | N | 6 | 2 |
| PRIDPOZ | C | 1 | 0 |
| FIKAINIS | C | 18 | 0 |
| FKIEKIS | N | 13 | 6 |
| TABR | N | 2 | 0 |
| PGRAFA | N | 2 | 0 |
| PSTORIS | N | 10 | 3 |

Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):

```json
[
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "SAM_EILUTE": "1",
    "DET_EILUTE": "1",
    "GRUP": "10",
    "IKAINIS": "A1",
    "KODAS": "S",
    "MATO_PAV": "KOMPL.",
    "KIEKIS": "15.000000",
    "KAINA": "1.0000",
    "PAVADIN": "Įeigos kontrolinis įrenginys"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "SAM_EILUTE": "1",
    "DET_EILUTE": "1",
    "GRUP": "20",
    "IKAINIS": "A1",
    "KODAS": "",
    "MATO_PAV": "žm.val.",
    "KIEKIS": "0.000000",
    "KAINA": "0.0000",
    "PAVADIN": ""
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "SAM_EILUTE": "1",
    "DET_EILUTE": "1",
    "GRUP": "30",
    "IKAINIS": "A1",
    "KODAS": "A1",
    "MATO_PAV": "KOMPL.",
    "KIEKIS": "15.000000",
    "KAINA": "350.0000",
    "PAVADIN": "Įeigos kontrolinis įrenginys"
  }
]
```

## FACT: nd25-04-14.dbf

SHA-256: `738c57f1fbc168732bfb3cd54df3a2d8d8a788f60222b968d2d2021b8e6a0471`

| Laukas | Tipas | Baitai | Dešimtainės vietos |
|---|---|---:|---:|
| KOMPLEKSAS | C | 10 | 0 |
| OBJEKTAS | N | 7 | 0 |
| SAMATA | N | 3 | 0 |
| SKYRIUS | N | 4 | 0 |
| SUSDARB2 | N | 3 | 0 |
| RANGOVAS | N | 4 | 0 |
| VYKDYTOJAS | N | 4 | 0 |
| POZ | N | 1 | 0 |
| K11 | N | 5 | 2 |
| K21 | N | 5 | 2 |
| K31 | N | 6 | 3 |
| K41 | N | 7 | 3 |
| K6 | N | 6 | 2 |
| SKDATANS | C | 4 | 0 |
| POZATL | C | 1 | 0 |
| KOEFTARI | N | 6 | 3 |
| POZFOND | N | 1 | 0 |
| PAVADIN | C | 180 | 0 |
| M29SAM | N | 3 | 0 |
| PERIOD | C | 4 | 0 |
| FAKRANG | N | 4 | 0 |
| FAKVYKD | N | 4 | 0 |
| FAKPOZ | N | 3 | 0 |
| PAR1PAV | C | 20 | 0 |
| PAR1POZ | N | 1 | 0 |
| PAR2POZ | N | 1 | 0 |
| PAR5POZ | N | 1 | 0 |
| PAR6PAV | C | 20 | 0 |
| PAR6POZ | N | 1 | 0 |
| PAR7POZ | N | 1 | 0 |
| PAR10POZ | N | 1 | 0 |
| PAR14POZ | N | 1 | 0 |
| PAR19POZ | N | 1 | 0 |
| PAR70POZ | N | 1 | 0 |
| PAR97PAV | C | 20 | 0 |
| PAR97POZ | N | 1 | 0 |
| PAR115POZ | N | 1 | 0 |
| PAR114POZ | N | 1 | 0 |
| PARXXPOZ | N | 1 | 0 |
| PARXXXPOZ | N | 1 | 0 |
| KAUPPOZ | N | 1 | 0 |
| XSAMATA | C | 8 | 0 |
| XSKYRIUS | C | 8 | 0 |
| STAMOBK | C | 6 | 0 |
| IVDAT | D | 8 | 0 |
| KODAT | D | 8 | 0 |
| SK5MEDZ | N | 10 | 5 |
| SK5MECH | N | 10 | 5 |
| PARISV | C | 10 | 0 |
| PARIV | C | 10 | 0 |
| PARVKOEF | N | 16 | 8 |
| PARPOZV | N | 1 | 0 |
| PAR47POZ | N | 1 | 0 |
| PARYPOZ | N | 1 | 0 |
| PARYYPOZ | N | 1 | 0 |

Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):

```json
[
  {
    "SAMATA": null,
    "SKYRIUS": null,
    "POZ": "2",
    "PAVADIN": "[ilgas objekto pavadinimas praleistas]"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": null,
    "POZ": "3",
    "PAVADIN": "Apsauginė signalizacija"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "POZ": "4",
    "PAVADIN": "Medžiagos"
  }
]
```

## FACT: od25-04-14.dbf

SHA-256: `c2fc450b8203c7264e4bf09c3faa3534b789e71983372bac929ca4ac19f7cf0f`

| Laukas | Tipas | Baitai | Dešimtainės vietos |
|---|---|---:|---:|
| KOMPLEKSAS | C | 10 | 0 |
| OBJEKTAS | N | 7 | 0 |
| POZYMIS | N | 3 | 0 |
| SKYRIUS | N | 4 | 0 |
| GRAFA4 | N | 13 | 3 |
| GRAFA41 | N | 13 | 3 |
| GRAFA5 | N | 13 | 3 |
| GRAFA51 | N | 13 | 3 |
| GRAFA6 | N | 13 | 3 |
| GRAFA61 | N | 13 | 3 |
| GRAFA7 | N | 13 | 3 |
| GRAFA71 | N | 13 | 3 |
| PROCENTAS | N | 6 | 2 |
| GRAFA | C | 4 | 0 |
| PAVADIN | C | 180 | 0 |
| PAVADIN1 | C | 120 | 0 |

Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):

```json
[]
```

## FACT: pd25-04-14.dbf

SHA-256: `781186cf94cbf4c1d28e76d2e5f55c1dadbcdbfe6f06b635121fe9717e9d58fe`

| Laukas | Tipas | Baitai | Dešimtainės vietos |
|---|---|---:|---:|
| KOMPLEKSAS | C | 10 | 0 |
| OBJEKTAS | N | 7 | 0 |
| RANGOVAS | N | 4 | 0 |
| SAMATA | N | 3 | 0 |
| SKYRIUS | N | 4 | 0 |
| SUSDARB1 | N | 3 | 0 |
| SUSDARB2 | N | 3 | 0 |
| POZYMIS | N | 1 | 0 |
| KODAS | C | 18 | 0 |
| MATOVNT | N | 3 | 0 |
| KIEKIS | N | 14 | 6 |
| KAINA | N | 12 | 4 |
| NGR4 | N | 2 | 0 |
| KODSUS | C | 10 | 0 |
| MVNTSUS | N | 3 | 0 |
| KOEFSUS | N | 10 | 5 |
| PAVADIN | C | 60 | 0 |
| MARKE | C | 180 | 0 |
| K5 | N | 9 | 5 |
| KAINBEK5 | N | 12 | 4 |
| SUS1 | C | 8 | 0 |
| SUS2 | C | 8 | 0 |
| XSAMATA | C | 8 | 0 |
| XSKYRIUS | C | 8 | 0 |

Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):

```json
[
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "POZYMIS": "3",
    "KODAS": "A1",
    "MATOVNT": "671",
    "KIEKIS": "15.000000",
    "KAINA": "350.0000",
    "PAVADIN": "Įeigos kontrolinis įrenginys"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "POZYMIS": "3",
    "KODAS": "A10",
    "MATOVNT": "642",
    "KIEKIS": "30.000000",
    "KAINA": "65.0000",
    "PAVADIN": "Elektromagnetinė spyna"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "POZYMIS": "3",
    "KODAS": "A11",
    "MATOVNT": "642",
    "KIEKIS": "1.000000",
    "KAINA": "2392.0000",
    "PAVADIN": "Tinklinis vaizdo įrašymo įrenginys"
  }
]
```

## FACT: sd25-04-14.dbf

SHA-256: `1bd6c83d8a1915f3b2f0f54f906d416d098ed1d8674a43b1e2e9c940b44d1f1b`

| Laukas | Tipas | Baitai | Dešimtainės vietos |
|---|---|---:|---:|
| KOMPLEKSAS | C | 10 | 0 |
| OBJEKTAS | N | 7 | 0 |
| RANGOVAS | N | 4 | 0 |
| SAMATA | N | 3 | 0 |
| SKYRIUS | N | 4 | 0 |
| SUSDARB1 | N | 3 | 0 |
| SUSDARB2 | N | 3 | 0 |
| SAM_EILUTE | N | 4 | 0 |
| DET_EILUTE | N | 4 | 0 |
| POZYMIS | C | 1 | 0 |
| IKAINIS | C | 18 | 0 |
| MATOVNT | N | 3 | 0 |
| IMLUMAS | N | 12 | 6 |
| KIEKIS | N | 13 | 6 |
| KATEG | N | 6 | 2 |
| UZMOKEST | N | 12 | 2 |
| MEDZIAG | N | 12 | 2 |
| MECHANIZ | N | 12 | 2 |
| K1 | N | 5 | 2 |
| K2 | N | 5 | 2 |
| K3 | N | 6 | 3 |
| K4 | N | 7 | 3 |
| K6 | N | 6 | 2 |
| K8 | N | 6 | 2 |
| K9 | N | 5 | 2 |
| VYKDYTOJAS | N | 4 | 0 |
| KIEKIS1 | N | 13 | 6 |
| KIEKIS2 | N | 13 | 6 |
| KIEKIS3 | N | 13 | 6 |
| METAI | C | 4 | 0 |
| KOEFPERV | N | 10 | 5 |
| DETEIL1 | N | 4 | 0 |
| SUS1 | C | 8 | 0 |
| MVNTS1 | N | 3 | 0 |
| KOEF1 | N | 11 | 5 |
| FIZKIE1 | N | 13 | 6 |
| SUS2 | C | 8 | 0 |
| KOEF2 | N | 11 | 5 |
| FIZKIE2 | N | 13 | 6 |
| POZYS | N | 1 | 0 |
| POSU | N | 1 | 0 |
| MEDZPOZS | N | 1 | 0 |
| XSAMATA | C | 8 | 0 |
| XSKYRIUS | C | 8 | 0 |
| PRIDPOZ | C | 1 | 0 |

Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):

```json
[
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "SAM_EILUTE": "1",
    "DET_EILUTE": "1",
    "POZYMIS": "S",
    "IKAINIS": "A1",
    "MATOVNT": "671",
    "KIEKIS": "15.000000"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "SAM_EILUTE": "2",
    "DET_EILUTE": "2",
    "POZYMIS": "S",
    "IKAINIS": "A2",
    "MATOVNT": "642",
    "KIEKIS": "15.000000"
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "SAM_EILUTE": "3",
    "DET_EILUTE": "3",
    "POZYMIS": "S",
    "IKAINIS": "A3",
    "MATOVNT": "642",
    "KIEKIS": "15.000000"
  }
]
```

## FACT: td25-04-14.dbf

SHA-256: `16944d33280c4ede6091a02c85ced293031a568ebd620bf9c3d35f14ae0872af`

| Laukas | Tipas | Baitai | Dešimtainės vietos |
|---|---|---:|---:|
| KOMPLEKSAS | C | 10 | 0 |
| OBJEKTAS | N | 7 | 0 |
| RANGOVAS | N | 4 | 0 |
| SAMATA | N | 3 | 0 |
| SKYRIUS | N | 4 | 0 |
| SUSDARB1 | N | 3 | 0 |
| SUSDARB2 | N | 3 | 0 |
| SUSDARB3 | N | 3 | 0 |
| DIML | N | 8 | 2 |
| DUZM | N | 12 | 2 |
| ISLMEDZ | N | 12 | 2 |
| ISLMEX | N | 12 | 2 |
| TIESISL | N | 12 | 2 |
| PPROC | N | 6 | 2 |
| K5 | N | 5 | 2 |
| MATOVNT | C | 10 | 0 |
| KIEKIS | N | 10 | 3 |
| PAVADIN | C | 60 | 0 |
| POZYMIS | N | 1 | 0 |
| KATEG | N | 5 | 2 |
| ATLYG | N | 6 | 2 |
| POZY | C | 1 | 0 |
| FAKRANG | N | 4 | 0 |
| FAKVYKD | N | 4 | 0 |
| METAI | C | 4 | 0 |
| ISLMEDZ3 | N | 12 | 2 |
| ISLMECH3 | N | 12 | 2 |
| UZMOKES3 | N | 12 | 2 |
| TIESISL3 | N | 12 | 2 |
| XSAMATA | C | 8 | 0 |
| XSKYRIUS | C | 8 | 0 |
| STAMOBK | C | 6 | 0 |
| NUOKO | C | 20 | 0 |
| KURSP | N | 1 | 0 |
| POZYMIS2 | N | 1 | 0 |
| SUMOSPAV | C | 30 | 0 |
| KOKIAISL | C | 5 | 0 |
| KURSPSP | C | 1 | 0 |
| KAIPSPSP | C | 1 | 0 |
| ZENKSK | N | 1 | 0 |
| ARSUMSP | N | 1 | 0 |
| PRIDPOZ | C | 1 | 0 |

Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):

```json
[
  {
    "SAMATA": "1",
    "SKYRIUS": "1",
    "MATOVNT": "",
    "KIEKIS": null,
    "PAVADIN": "",
    "POZYMIS": null
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "2",
    "MATOVNT": "",
    "KIEKIS": null,
    "PAVADIN": "",
    "POZYMIS": null
  },
  {
    "SAMATA": "1",
    "SKYRIUS": "9999",
    "MATOVNT": "",
    "KIEKIS": null,
    "PAVADIN": "Papildomų medžiagų vertė   3.00%",
    "POZYMIS": "1"
  }
]
```

## FACT: jungčių patikra šiame rinkinyje

Kandidatinis raktas: `KOMPLEKSAS, OBJEKTAS, RANGOVAS, SAMATA, SKYRIUS, SUSDARB1, SAM_EILUTE, DET_EILUTE`.
sd eilučių 104, unikalių raktų 104, dd eilučių 391.
dd be sd rakto: 0. dd GRUP=10 įrašų: 104, unikalių raktų: 104.
sd be sutampančio dd GRUP=10 kodo ir kiekio: 0.
dd GRUP pasiskirstymas: {'10': 104, '20': 104, '30': 157, '40': 26}.

## INFERENCE: reikšmės, ribotos šiam archyvui

- sd panašu į sąmatos pozicijas; pavadinimo lauko nėra. dd GRUP=10 duoda
  tos pačios pozicijos istorinio aprašymo tekstą ir tekstinį vienetą.
- dd GRUP=20/30/40 panašu į darbo / medžiagų / mechanizmų išteklius.
  Tai hipotezė pagal laukus ir pavyzdžius, ne patvirtinta SISTELA specifikacija.
- pd panašu į išteklių kainų sąrašą; KODAS nėra automatiškai darbų normatyvas.
- nd turi projekto, sąmatų ir skyrių pavadinimus; POZ lygmenų semantika dar nepatvirtinta.
- td panašu į sumas / išlaidų grupes; skaičiavimo taisyklės nepatvirtintos.
- od tuščias: schema patvirtinta, įrašų semantika nenustatyta.

## UNKNOWN / TODO

- Originalūs normatyvų katalogo pavadinimai. dd PAVADIN gali būti pervadintas.
- Pilnas MATOVNT kodų žodynas ir 100m konversijų taisyklės.
- nd/pd/td/od tarpusavio jungtys, null ir koeficientų semantika už šio archyvo ribų.
- DBF archyvo atkūrimo, indeksų ir memo reikalavimai SISTELA programoje.
- Sąmatos kainodaros atkartojimas, rašymas ir round-trip neįgyvendinti.

## Saugus tolimesnis importas

Galima pateikti vartotojui sd + dd GRUP=10 istorinio kodo/aprašymo kandidatus
su šaltinio nuoroda. Jų negalima automatiškai laikyti patvirtintais mappingais ar
originaliais normatyvų pavadinimais. Reikalinga žmogaus patvirtinimo eiga (6 fazė).


## FACT: PHASE 6 papildoma kardinalumo patikra (2026-09-29)

Pagal KOMPLEKSAS/OBJEKTAS/RANGOVAS/SAMATA rasta 3 unikalios nd POZ=3 antraštės
su SKYRIUS=null. Pridėjus SKYRIUS – 6 unikalios nd POZ=4 skyrių antraštės.
Visos 104 dd GRUP=10 pozicijos turi po vieną iš šių sąmatų ir skyrių.
nd POZ=2 su SAMATA=null pagal KOMPLEKSAS/OBJEKTAS atitinka vieną objektą.

Antraščių tekstai „Medžiagos“ / „Darbai“ pasiskirsto: sąmata 1 – 20/10 pozicijų,
sąmata 2 – 20/13, sąmata 3 – 25/16. Darbų skyriuose 39 pozicijos ir 34 skirtingi
IKAINIS kodai. Visų trijų sąmatų nd KODAT reikšmė 2026-08-21; ji neįrodo paskutinio
normatyvo panaudojimo datos. Darbo sistemos AS/GSS/ER yra interpretacija iš sąmatų
pavadinimų, ne DBF sistemų klasifikatoriaus faktas.

Šie faktai regresiškai tikrinami tests/test_history.py. Kitų archyvų kardinalumas
perskaičiuojamas importuojant; neatitikimai pažymimi AMBIGUOUS. Pilnos nd/pd/td/od
semantikos ir katalogo originalių pavadinimų ši patikra neįrodo.
