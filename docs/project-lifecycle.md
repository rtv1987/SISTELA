# Projektų šiukšlinė

Projekto viršuje pasirinkite **Į šiukšlinę**, tada patvirtinkite dialoge. Projektas
dingsta iš įprasto sąrašo; jo eilutės, peržiūra, konversijos, dokumentai ir suvedimo
eiga lieka išsaugoti. Šiukšlinėje projekto redaguoti negalima.

Kairėje pasirinkite **Šiukšlinė → Atkurti**. Projektas grįžta į sąrašą su ankstesne
būsena. **Ištrinti visam laikui** atveria kitą dialogą: būtina įvesti tikslų projekto
pavadinimą ir paspausti galutinį patvirtinimą. Šio veiksmo atšaukti negalima.

Galutinai šalinami tik projekto duomenys: eilutės ir jų review/conversion/entry
būsena, skyriai, reikalavimai, importo įrašai, grid undo ir konkrečios eilutės mapping
patvirtinimų auditas. Projektui priklausančios PDF/XLSX kopijos šalinamos tik jeigu
jų nebenaudoja kitas projektas, įskaitant projektą šiukšlinėje. Jei Windows neleidžia
pašalinti užimtos kopijos, rodomas pranešimas; projekto DB įrašai jau pašalinti.

Išlieka kiti projektai, visi istoriniai DBF importai, istorinių kandidatų patvirtinimai,
jų įrodymai ir bendri pakartotinai naudojami SISTELA atitikmenys. Bendro atitikmens
patvirtinimų skaičius lieka istoriniu naudojimo rodikliu. Originalūs vartotojo failai
neliečiami. DBF failai niekada nerašomi; Package Text lieka EXPERIMENTAL.

API: `GET /trash`; `POST /projects/{id}/trash`; `POST /projects/{id}/restore`;
`POST /projects/{id}/delete` su `{"confirmation":"tikslus pavadinimas"}`.
Aktyvaus projekto galutinis trynimas grąžina 409, netikslus pavadinimas — 422.
Migracija `008_project_trash` tik prideda nullable `projects.deleted_at`.

Regresijos: backend tikrina DB įrašus, bendrą istoriją, atitikmenis, bendras kopijas ir
originalius failus; frontend — dialogus ir patvirtinimus; Playwright — atkūrimą ir
istorijos išlikimą po ištrynimo. Ekranai: `screenshots/phase8-trash.png` ir
`screenshots/phase8-delete-confirmation.png`.
