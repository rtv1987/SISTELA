# 0.2.2 maintenance investigation

## Real project — all 12 rows

The supplied PDF contains no prices. No full-row normative replacement is proven for these rows. Historical G1/G2/G4 retain evidence but are not normative catalog codes. The old work selection M10-448-6 describes control-room equipment adjustment, not the full requested scope; a generated work code now avoids that substitution.

| Source description | Model | Type | Quantity/unit | Selected code | Provenance | Normative match | Price source | Explicit price required | Remaining blocker |
|---|---|---|---|---|---|---|---|---|---|
| Adresinis kontrolinis įrenginys 2 kilpų | SmartLoop/2080 | Material | 1 kompl. | G1 | Historical G1 | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Akumuliatorius 12V 17Ah | Ultracell | Material | 2 vnt. | G2 | Historical G2 | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Adresinė vidaus sirena su blykste | ES2021RE | Material | 10 vnt. | G4 | Historical G4 | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Adresinė lauko sirena su blykste | ES2021RE | Material | 1 vnt. | AFD089DA4D0673BD | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Adresinis ranka valdomas pavojaus signalizavimo įtaisas | EC0020+WCP00 20 | Material | 9 vnt. | AEAB2DCF38432D31 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Adresinis dūmų detektorius su baze | ED100+EB0010 | Material | 68 kompl. | A8908A3A5CC59987 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Įėjimų/išėjimų modulis | EM344R | Material | 4 vnt. | AAB77373C66512D8 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Gaisrinės signalizacijos kabelis 1x2x1,0 mm2 | HTKSHekw | Material | 1150 m | A2FF0B013462E8A1 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| GSM modulis | G17F | Material | 1 vnt. | ADD7DA3F34C877E5 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| PVC vamzdelis D20, su tvirtinimo elementais | Pipelife | Material | 1150 m | AA1D34ECB2D77074 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Papildomų medžiagų komplektas | — | Material | 1 kompl. | A495989E3715E811 | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |
| Darbai pagal sudėties žiniaraštį, dokumentacijos parengimas, paleidimas ir derinimas | — | Work | 1 kompl. | W6B7131CE5E9DE1B | Persistent generated custom code | None semantically verified | None current/authorized | Yes — C | Actual price; review code/scope |

All 11 material price demands are supported by the documented custom-position form, given the currently verified matches. They were not removed simply to make export pass. The new work-scope finding adds one genuine custom work price/scope exception: 12 unresolved fields in total. No current price was inferred from base prices dated 2001/2005/2020 or historical use.

Examples rejected: 7 Ah battery versus 17 Ah; outdoor siren with a different model; generic smoke detector in vnt. versus detector+base in kompl.; PVC d20 without fixing elements versus the complete requested assembly; Pipelife PEX-AL-PEX is not PVC conduit. Full-catalog model searches found no SmartLoop, Ultracell, ES2021RE, EC0020/WCP00, ED100/EB0010, EM344R, HTKSH, or G17F match.

## Previous text exceptions

| Original output (source retained) | Prepared TXT text | Rule |
|---|---|---|
| Gaisrinės signalizacijos kabelis 1x2x1,0 mm2 | Gaisrinės signalizacijos kabelis 1x2x1.0 mm2 | decimal_comma_to_dot |
| PVC vamzdelis D20, su tvirtinimo elementais | PVC vamzdelis D20; su tvirtinimo elementais | list_comma_to_semicolon |
| Darbai pagal sudėties žiniaraštį, dokumentacijos parengimas, paleidimas ir derinimas | Darbai pagal sudėties žiniaraštį; dokumentacijos parengimas; paleidimas ir derinimas | list_comma_to_semicolon |

These were delimiter exceptions, not excessive description length. The unproven 120-character row limit was also removed; hierarchy limits remain. The complete text is preserved, without silently truncating words. See ADR 0012 and the supplied manual printed pp.46–48.

## Local acceptance artifacts

- `data/exports/ACCEPTANCE_022/verified/investigation.json`: all source/model/unit/code/history/catalog/price/provenance details.
- `REAL022.prepared.json`: every safely derived real-project field.
- `REAL022.validation.json`: genuine remaining blockers; no punctuation blocker.
- `ZERO022.TXT`: documented custom-material syntax with explicitly experimental zero, not a market price.
- `DBF022.state.json`: current project field classifications and precise blockers.

**No importable REAL022.TXT was fabricated:** the real prices are absent. The prepared JSON is not an importable package. After genuine prices/scope decisions, the ordinary whole-estimate export produces the TXT without manual Entry Mode.

## Darius procedure

1. Install 0.2.2 and open the project list.
2. Import the actual PDF; verify 12 rows, review automatic/custom codes and the complete work scope. Original descriptions and quantities must remain intact.
3. Supply actual custom-position prices (or explicitly choose a valid existing catalog position). Export the whole estimate once. Match SISTELA parameter 89 to the application setting.
4. In a disposable SISTELA estimate: Informacijos įvedimas → Informacija pakete → Tikrinti informaciją → Formuoti sąmatinę informaciją. Compare all codes, descriptions, units, quantities and prices.
5. Separately load ZERO022.TXT into an empty disposable estimate. Record whether validation accepts zero, whether formation succeeds, whether quantity 1 / unit vnt. / NGR 12 survive, and whether price can then be entered and recalculated. Do not treat a successful parse alone as pricing acceptance. Do not use this zero-price experiment for a real estimate.
6. Do not try an omitted-price custom record: that syntax is not documented. Record the exact SISTELA version, parameter 89, errors and resulting row for the zero experiment.
7. DBF: current-project export remains blocked. Only the isolated historical-clone experiment may be tested; never overwrite working or golden archives.

## Packaging root cause

The affected local folder has 36 of 556 required files; its executable matches 0.2.0, and the entire SQLAlchemy folder is absent. A copied reproduction produces no runtime state. Original 0.2.1 portable contains the reported extension and starts from a clean external location. The cause of the partial deployment itself is unknown; do not confuse this with a proven PyInstaller omission.

0.2.2 collects the SQLAlchemy runtime modules and upstream Python fallbacks. Setup verifies all bundled file hashes and frozen dynamic imports/SQLite before reporting success, and repairs using its own new runtime. Shutdown no longer imports the database stack. Clean portable tests include all native SQLAlchemy extensions being deliberately unavailable in a disposable copy.

## Proven versus pending

Software proofs and artifact hashes are recorded in release-0.2.2.json after verification. Real SISTELA acceptance remains pending for full-estimate TXT, long description retention, zero-price custom positions, and DBF calculations/identifiers. No prices or unknown DBF formulas are invented. Rankinis perkėlimas remains fallback only.

## Final verification and release artifacts

- Backend: **247 passed**, including required private fixtures. The ordinary
  release PDF subset separately passed **52** tests (already included in 247).
- Frontend: **59 passed**; Playwright: **16 passed**. **322 total**.
- Added 13 backend cases, one frontend case and one browser case; updated the
  real-catalog browser regression and invalid-text tests to reflect documented
  behavior. New checks cover three text corrections, long descriptions, price
  categories, unsafe work matching, source preservation and install integrity.
- Ruff, frontend lint, TypeScript, production build, diff whitespace check and
  Alembic check passed. Head: `012_bulk_preparation`; **no new migration**.
- Environment: initial full-suite IPv4 tests hit Windows socket exhaustion;
  temporary IPv6 test harnesses passed all assertions. Ordinary packaged IPv4
  startup and release PDF pytest checks passed. No workaround ships.

| Packaged check | Result |
|---|---|
| Frozen EXE launch, health, static UI, migrations | PASS |
| Frozen real PDFs (21 and 12 rows), real catalog/history, whole-estimate TXT/XLSX | PASS |
| Clean extracted Portable outside repository, sanitized environment | PASS |
| Portable relaunch and project persistence | PASS |
| All SQLAlchemy native extensions removed: Python fallback launch | PASS |
| Manifest rejects a partial bundle | PASS |
| Actual Setup installation, shortcut and installed launch | PASS |
| Running-app reinstall and damaged SQLAlchemy installation repair | PASS |
| Installed relaunch; uninstall retains user DB and unrelated file | PASS |
| 0.2.0 data copy upgrade, backup and preserved projects | PASS |
| 0.2.1 data copy upgrade and preserved projects | PASS |

Five packaging smoke scenarios passed. Evidence locations and detailed metadata:
[release-0.2.2.json](release-0.2.2.json). No licensed DBF/PDF/database files ship.
All four 0.2.0/0.2.1 Setup/Portable hashes still match their prior values.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `dist/windows/SISTELA-Assistant-Setup-0.2.2.exe` | 53,263,749 | `69394b2057b0f24233c729ffd5275bf1337436dd49ebd7e1e6289eb5c3a87825` |
| `dist/windows/SISTELA-Assistant-Portable-0.2.2.zip` | 71,053,416 | `0da6854935d3ab2ecacbc9f8ccc31a248e1044a2594d88866b617feac6dea3ba` |

Paths above are relative to `C:\Users\rtv19\Documents\GitHub\SISTELA`.
[Complete changed-file inventory](release-0.2.2-files.md).
Four new screenshots were created and visually inspected:
`022-real-grid.png`, `022-real-export.png`, `022-real-dbf.png`,
`022-txt-result.png` in `docs/screenshots`. Existing regression screenshots were
refreshed. The TXT-result screenshot uses explicitly priced synthetic data,
not fabricated prices for the actual project.

Next real-world test: Darius reviews the 12-row scope and supplies genuine custom
prices or valid existing catalog selections, exports once, then validates/forms
that whole TXT in a disposable SISTELA estimate. Compare every resulting code,
unit, quantity, full description and price. Separately test ZERO022.TXT; retain
its zero-price status as experimental until both formation and repricing work.
