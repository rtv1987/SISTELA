# ADR 0010 — Local catalog and Phase 10 workflow

Implemented architecture: preserve the structural PDF pipeline and all Phase 9 work;
verify both private PDF fixtures; discover and hash the licensed normative sources;
add a versioned read-only catalog import with normalized records, explicit relations
and an offline FTS index; expose local folder/ZIP import and search in Settings.
Then integrate catalog-backed automatic choices and correction learning into existing
mapping services, retire mandatory mapping confirmation while retaining explicit unit
conversion, and introduce one export model for both TXT and DBF validation.

TXT generation requires the official grammar and parameter documentation. Financial
DBF fields remain blocked wherever their mandatory semantics are UNKNOWN. Neither
exporter writes into SISTELA. Licensed source DBF/FPT/IDX/ZIP files and derived user
indexes are excluded from packaging. Sources are hashed before/after ingestion.

Target release is explicitly 0.2.0. Existing versioned installers remain immutable.
Implementation, restrictions and validation are detailed in sistela-export-architecture.md and phase10-results.md. Real SISTELA acceptance is still pending for both export formats.
