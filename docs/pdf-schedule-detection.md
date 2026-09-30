# Structure-first schedule import

The parser discovers table-like regions using pdfplumber native tables, PyMuPDF
coordinates and repeated loose rows. Description, quantity, unit and optional
position/model columns are inferred from their contents and geometry. Headings are
supporting evidence, never an eligibility gate. No filename, company, system,
page number or expected fixture row count is a production parsing rule.

Candidates carry positive and negative signals and region provenance. Repeated
headers, wrapped rows and compatible consecutive pages are reconstructed before
classification. Overlapping candidates are deduplicated. Strong candidates select
automatically; competing credible candidates persist previews for user selection.
The selection endpoint checks project ownership, document checksum, parser version
and one-time selection. Unclassified rows remain Other, not invented work rows.

Private real regressions: `2024-10-XX-TDP-GSS.pdf` gives 21 rows (11 materials,
10 works); `2024.07-616SR-BCB-AG.pdf` gives 12 (11 materials, one work). The second
also succeeds with heading evidence removed. Tests additionally cover reordered
columns, borderless and wrapped tables, multi-page and competing tables. Raw PDFs
remain local and excluded from installer and source control.

Classification and automatic code selection are distinct stages. Confirmed history
can help classify otherwise ambiguous row types. Once extraction is persisted, the
mapping service fills available codes; this does not manufacture source rows or
alter source quantity, unit, raw text, page or document identity.
