# ADR 0002: Decimal ir šaltinio atsekamumas

SQLite NUMERIC gali konvertuoti dešimtainę reikšmę į binary float.
Kiekius ir kainas saugome kanoniniu Decimal tekstu, skaičiuojame Python Decimal,
HTTP perduodame eilutėmis. SQL tekstinis rūšiavimas skaičiams netinka;
būsimas grid rūšiuos skaitines reikšmes. Nenaudojame SQL SUM šiems laukams.
Laikome originalius langelius, dokumento tekstą, SHA-256, puslapį, parserio versiją.
Kodas ir trys pavadinimai yra nepriklausomi. Importas visada reikalauja peržiūros.
