# ADR 0003: tik DBF skaitymas

Naudojama dbfread su strict decoding ir Decimal laukų parseriu.
Koduotė perduodama aiškiai; šio fixture cp1257 pagrindžia lietuviško teksto palyginimas
su XLSX, nors LDID=3 nurodo cp1252. Tai nėra universali visų archyvų taisyklė.
Analizė išveda laukus, pavyzdžius ir skaitinius jungčių patikrinimus.
Normatyvinis kodas nėra vartotojo pervadintas pavadinimas. Historiniai duomenys nėra
patvirtintas normatyvų katalogas. Rašymas užblokuotas iki SISTELA round-trip eksperimento.
