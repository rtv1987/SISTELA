# ADR 0008 — Evidence-bound DBF export

Accepted 2026-09-29, supersedes the blanket DBF-writer prohibition for isolated tests.
The user's real interchange evidence authorizes generating new archive files, while
golden originals and live SISTELA directories remain outside the write boundary.

Implement a separate physical C/N/D FoxPro model and explicit serializer. Preserve
opaque metadata, physical ordering, deleted flags, blank values, cp1257, LDID and
empty OD layout. Do not reuse the lossy historical-knowledge DB as an archive backup.
Historical parsing remains read-only. No additional DBF writing library/default dialect.

Publish only after in-memory serialization, reparse, proven relationship checks and
semantic comparison pass. Publish an entire new folder with manifest atomically;
never overwrite. API receives bytes, not filesystem destinations. UI offers a clearly
experimental six-file clone ZIP; controlled mutations are developer-only.

The requested preferred quantity mutation cannot safely be calculated from the
available evidence. dd/pd/td financial dependencies are UNKNOWN; use one header
description change for TEST_B and block numeric mutations. This is an explicitly
narrower experiment, not proof that quantity changes import correctly.

PROJECT_EXPORT has input preparation, deterministic **proposed** keys, field-fit and
review validation, but no generated DBF archive until calculation, MATOVNT, naming
and collision rules are proven. Export requests fail closed with concrete blockers.
Do not write zeroes into unknown required fields to make a superficially valid archive.
Both real A/B acceptance results are required before considering capability promotion;
financial/project export still requires additional evidence. Entry Mode remains usable.

See [format evidence](../sistela-dbf-export.md) and [real test instructions](../sistela-dbf-roundtrip.md).
