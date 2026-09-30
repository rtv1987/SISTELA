# Privatūs importo pavyzdžiai

Čia galima padėti `2024-10-XX-TDP-GSS.pdf` (arba užduotyje minimą variantą su `(1)`)
ir `pvz.xlsx`. Testai taip pat randa originalus repo šaknyje.
Failai neredaguojami ir neįtraukiami į Git. Kontrolinės sumos – ../manifest.json.

Struktūrinio PDF parserio regresijai taip pat reikalingas originalus
`2024.07-616SR-BCB-AG.pdf` (12 eilučių: 11 medžiagų, 1 darbas).
Šis failas dar nepateiktas. Jo testai yra `tests/test_pdf_structure.py`;
`--require-fixtures` jo nebuvimą laiko klaida. Gavus originalą, įrašyti jo tikrą
SHA-256 į manifestą. Negeneruoti pakaitinio „realaus“ dokumento.
