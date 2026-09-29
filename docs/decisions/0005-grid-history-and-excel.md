# ADR 0005 – Lentelės operacijos, istorija ir Excel

2026-09-29. Priimta.

- React/TanStack Table ir Radix Tabs; vietinis FastAPI aptarnauja sukompiliuotą UI.
- Keitimai siunčiami nuosekliai ir tikrinami pagal eilutės versiją. Masinis keitimas
  yra viena SQLite transakcija. Trinimas loginis; paskutinio lentelės veiksmo undo
  galimas tik jei vėliau pakeistos eilutės nesukelia versijų konflikto.
- Kopijos išlaiko šaltinio duomenis, tačiau reikalauja naujo normatyvo patvirtinimo.
- Susiejimų istorija mokosi tik iš žmogaus patvirtinimų. Sistema, normalizuotas
  tekstas, normatyvinis vienetas ir kodas sudaro unikalų raktą. Naujesnis pataisymas
  turi prioritetą; atskiri įvykiai išsaugo ankstesnį ir naują kodą.
- `m` ir `100m` nesutampa. Perskaičiavimą vartotojas atlieka lentelėje ir patvirtina.
  Įvertis yra euristika, ne statistinė tikimybė. Normatyvų katalogas nesukuriamas.
- Entry Mode kopijuoja tik vartotojui paprašius. `entered_at` yra žmogaus žyma,
  ne SISTELA patvirtinimas; po eilutės redagavimo ji išvaloma.
- XLSX yra darbo duomenų mainai, ne patvirtintas SISTELA importas. Darbo lapas,
  antraštės eilutė ir kolonų susiejimas pasirenkami prieš importą. Blogos eilutės
  blokuoja importą, kol vartotojas aiškiai leidžia dalinį importą.
- OOXML skaičiai skaitomi kaip tekstas → Decimal. Importo tikslumas 6 skaitmenys
  po kablelio, ROUND_HALF_UP; bet kuris apvalinimas registruojamas įspėjimu,
  originali reikšmė išlieka source_raw_text. Vienetai nekonvertuojami.
- Formulės nevykdomos. Eksporte vartotojo tekstas įrašomas kaip tekstas;
  daugiau nei 15 reikšminių skaitmenų turintis skaičius taip pat eksportuojamas
  tekstu su perspėjimu, kad Excel neprarastų tikslumo.
- Importo atrankos tapatybė: failo checksum + lapas + antraštė + mapping.
  Mapping statusas ir suvedimo žymos neperduodamos per XLSX.
- Package Text rašymas lieka užblokuotas; DBF lieka read-only.
