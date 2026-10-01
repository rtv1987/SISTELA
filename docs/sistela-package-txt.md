# Informacija pakete — EXPERIMENTAL TXT

Primary local sources: `data/documents/NAUJA_INSTR_ SAMATU_2011.PDF`, printed
pages 46–48 (package coding rules), and `PARAMETRAI_SKAIČIAVIMAMS.PDF`, parameter
89. Original files remain read-only. This is a dedicated exporter; the older
lossless PackageTextParser/developer experiment remains separate.

## FACT — documented records

One file contains one local estimate. Filename: at most eight letters/digits.
Hierarchy records: `1,complex,name`, `2,object,name,YYYYMM`,
`3,estimate,name,YYYYMM`, `4,section,name`. Code lengths are 10/7/3/3 and name
lengths 120/120/60/60 respectively. Type 6 uses an 18-character code and quantity
5.6; equipment quantity uses 5.3 and a unit up to 10 characters.

Implemented forms:

```
6,CODE,quantity
6,CODE,quantity,P=output description
6,CUSTOM,quantity,<S,unit>,P=description,R=7,price,NGR
6,EQUIPMENT,quantity,<I,unit>,P=description,I=price
6,PARAMETRIC,quantity,G=x,y
7,2,resource-code,-0.23
```

Custom marks S/G/I, NGR 1–12, rate coefficients K1–K4 and section coefficients
K11/K21/K31/K41/K6 are supported. Type 7 is restricted to the illustrated
four-field existing-resource adjustment, flags 2/3, with a resolved local catalog
relationship. Custom resource/full price forms are blocked: the manual's header
and prose do not establish an unambiguous complete field sequence.

## Validation and explicit limits

`validate_txt_export` checks hierarchy, field widths, duplicate sections, required
codes, quantities, units, explicit conversions, prices for custom entries,
parameterized-rate G values and allowed syntax. Text is never truncated. Commas,
newlines, control characters and reserved syntax in user fields are rejected;
quoting/escaping such text is not documented. Prices are never invented.

The experimental encoding is cp1257 with CRLF, to be checked in Darius's real
SISTELA. **DERIVED conservative profile limits**, not documented package maxima:
120 characters for row descriptions, price 7.4 and resource norm 5.6. Longer or
more precise forms remain blocked until verified. Section/rate coefficient and
resource adjustment options are exposed through the typed export profile API;
the work table exposes marks/NGR and G only in advanced row details. The normal export view has bulk TXT/DBF buttons; hierarchy settings are optional.

Generation round-trips through `parse_generated_txt`, comparing record structure,
codes and exact Decimal target quantities. This proves our format consistency,
not that SISTELA has accepted it. No production status promotion is automatic.

## Parameter 89

The local setting is Unknown/0/1 and never inferred from the user's installation.
Unknown blocks TXT. Parameter 0 exports the explicitly selected target quantity.
Parameter 1 is allowed for unscaled identical units; a converted or scaled-unit
row is blocked because SISTELA may convert it again. For m→100M, confirm the
conversion in Assistant, set **actual SISTELA parameter 89=0**, then save that
same setting in Assistant. Source quantity and source unit remain intact.

## Darius acceptance

Use only a dedicated test complex. The small `data/exports/TEST_TXT/TESTTXT.TXT`
is generated from a code verified in the local catalog. Check the README/manifest
beside it for the exact code, quantity, source and required 89 setting. In SISTELA:
Informacijos įvedimas → Informacija pakete → choose the editor → paste the text
→ Tikrinti informaciją → Formuoti sąmatinę informaciją. Record diagnostics and
verify the resulting rate, quantity and unit. Do not assume an undocumented
direct-file-opening workflow. TXT remains EXPERIMENTAL until that real test passes.

## 0.2.1 product workflow

Custom codes, S/I marks, generic NGR 12, hierarchy, section codes, filename and month
are prepared automatically and persisted. Parameter 89 is configured once under
Nustatymai → SISTELA. No manual readiness or entered-progress step is needed.
A full estimate is one TXT download. Rankinis perkėlimas is only a fallback.

Missing custom prices remain real exceptions: the manual requires a price for
that form, and zero/omitted-price placeholders are not established. Average-price
catalog positions use the documented price-omitting form. See
[product decision](decisions/0011-bulk-product-workflow.md) for facts and limits.
