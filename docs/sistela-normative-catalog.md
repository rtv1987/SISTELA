# Local normative catalog

## FACT — supplied source

The licensed local folder contains 20 DBFs, one FPT and 19 IDX files. Original
SHA-256 values are in `samples/normative-manifest.json`; complete field definitions
and table record counts are in `sistela-normative-schema.json`. No raw licensed
tables or derived personal index are bundled in Setup or Portable.

The read-only importer uses cp1257, validates DBF record boundaries and reads the
FPT memo companion. IDX files are unnecessary to the derived index. Folder and ZIP
imports fingerprint DBF/FPT contents and are idempotent. ZIP paths, duplicate
basenames, file counts and expanded sizes are checked. Sources are hashed again
before commit; partial imports roll back. Reimport selects an existing identical
catalog; a different version retains the old version and activates the new one.

Projection counts in the supplied source:

| Kind | Rows |
|---|---:|
| Rates (`erer`) | 35,035 |
| Resources (`resursai`) | 22,748 |
| Products (`gaminiai`) | 8,237 |
| Resource price records (`samkainw`) | 22,027 |
| Hierarchy (`nturinys`) | 3,824 |
| Memo texts (`ik_teksw`) | 7,628 |
| Coefficients (`koef`, `koefkoef`) | 5,136 |
| Other preserved reference records | 191,650 |

`NormativeCatalogSource` retains timestamp, fingerprint, schema diagnostics and
manifest. `NormEntry` retains kind, code, normalized and original descriptions,
unit/identifier, category, file and physical record number, plus the original
decoded payload. `NormRelation` contains 88,576 resource links, including explicitly
unresolved links. These are shared normalized tables with a kind discriminator,
not separate ORM tables for every proprietary file.

## DERIVED — joins and unit labels

`erer.IKAINIS` identifies rates. `medznorm.IKAINIS` matches 27,986/29,120 source
rows; `MEDZIAGA1/2` and `NORMA1/2` are retained separately. `mechnorm.IKAINIS`
matches 16,219/16,653; only 33 mechanism resource codes match `resursai`.
`ikaimedz.IKAINIS` matches only 198/20,759 while 20,758 material references match.
Unmatched codes remain unresolved, not fabricated entries.

`erer.MATO_VNT`, `resursai.MVNT` and `gaminiai.MVNT` use numeric unit identifiers.
Labels are derived from matching `samkainw.KODMAT/MATOVNT` and
`orkainos/orkvisos.MVNT/MATOVNT`. Of 31 identifiers, 24 have unambiguous normalized
labels and seven conflict. 25,803 rates have an unambiguous label. Conflicts retain
all candidate labels and source evidence; the projected unit remains empty.
N50-270 has identifier 796 and resolves to vnt. in this source.

`nturinys` retains levels, ranges and descriptions. Category search uses the code
prefix as a derived grouping, not a claim of a complete proprietary hierarchy.
`koef`, `koefkoef`, `nuoroda`, `pokyciai`, `med`, `antkain`, `eremazom` and price
tables retain their payloads. `fonddarb` resembles estimate detail with financial
fields; it is reference evidence, not a verified universal rate table.

SQLite FTS5 indexes normalized Lithuanian text, codes and category. Queries use
quoted normalized prefix tokens, exact-code matches first, optional kind/unit/
category filters, and bounded results. Everything runs offline. The UI exposes
folder/ZIP import, search, original payload and linked resource provenance.

## UNKNOWN

Full proprietary hierarchy/range interpretation, missing mechanism catalogs,
conflicting units, coefficient applicability, parameter-rate variants and the
meaning/current validity of dated prices remain unresolved. No price is selected
automatically and no resource or calculation formula is synthesized. The original
WeTransfer ZIP was not supplied here: ZIP tests use an archive built from local
fixtures, and the actual supplied source is the unmodified folder.
