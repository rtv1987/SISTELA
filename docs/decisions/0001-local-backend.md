# ADR 0001: lokalus modulinis backend

Priimta: FastAPI, SQLAlchemy, SQLite ir Alembic. API tik loopback.
Parsers nepriklauso nuo persistence. React UI atskira 4 fazė.
Alternatyvos: Tauri dabar didintų pakavimo darbą prieš patikrinant importą;
cloud netinka numatytajam konfidencialių dokumentų režimui.
Pasekmė: vieno naudotojo lokali DB; tinklo prieigai ateityje reikės autentifikacijos.
