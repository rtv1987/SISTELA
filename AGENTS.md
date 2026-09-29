# SISTELA Assistant

- Local Windows application. Keep the domain independent from SISTELA integration.
- Never modify original PDF/XLSX/DBF fixtures, including those currently in the repo root.
- No DBF writer, SISTELA folder writes, unverified package formats, or UI automation.
- Distinguish FACT, INFERENCE and UNKNOWN in reverse-engineering documents.
- Project description, normative code, original normative description and output description
  are separate fields. Historical renamed text is not an original catalogue description.
- Decimal for quantities and money. Preserve units such as `100m`.
- No document content in logs. No cloud transfers or external AI by default.
- Use Alembic migrations, not runtime create_all. Keep migrations independent of live models.
- Run `.venv/Scripts/python.exe -m pytest` and `.venv/Scripts/ruff.exe check .`.
- With private samples available run pytest with `--require-fixtures`; absent samples must
  be explicit skips, never generated substitutes for a real regression.
- Document major design decisions in docs/decisions and phase results in docs/progress.md.
