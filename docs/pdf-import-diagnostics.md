# PDF import diagnostics

Open **Importo informacija** after importing a PDF. If selection is required, no
estimate rows have been added. Review the page range, preview, units, quantities
and row count, then choose **Pasirinkti lentelę**. The choice remains available
after reload. Selecting creates ordinary unconfirmed estimate rows; continue in
Review Queue as before.

Expand **PDF importo diagnostika** to inspect every candidate, including rejected
ones. Each has a stable ID for that parser version/document, method (`native`,
`geometry`, `loose`), page/bounds, column indices and evidence confidences, signed
score contributions and an outcome. `DUPLICATE` and `CONTINUATION` identify the
candidate that retained that physical region. Scores are deterministic evidence
weights, not measured probabilities. No work/material ratio is evaluated.

Use this evidence when diagnosing new customer files. Do not add filenames,
page constants or exact title gates. Keep the original private PDF and its hash;
add a fixture test of quantities, units, classifications and provenance. Also
test an extraction representation with heading/index evidence removed.

Current private fixture locations are repository root or `samples/input/`:

- `2024-10-XX-TDP-GSS.pdf`: 21 rows, 11 materials, 10 works.
- `2024.07-616SR-BCB-AG.pdf`: required but not yet supplied; acceptance expects
  12 rows, 11 materials, one aggregate work row. Tests also cover removed heading
  evidence. The actual original must be added; a generated substitute is invalid.

Run `scripts/test.ps1 -RequireFixtures -E2E` before release. Missing private files
are failures with this switch. Development without it reports explicit skips.
Only after both fixtures pass, set canonical VERSION to 0.1.1 and run
`scripts/build-windows.ps1`. The build runs the real frozen EXE against both PDFs
through `verify_windows_release.py` / `smoke_windows.py` and verifies the version.
