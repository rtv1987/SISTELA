"""EXPERIMENTAL writer: only isolated six-file clones and a bounded text experiment.

Production PROJECT_EXPORT is deliberately blocked on unproven SISTELA semantics.
"""
import copy
import json
import re
import shutil
import struct
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
from pathlib import Path

from .dbf_archive import ROLES, compare_archives, parse_table, read_archive, validate_relationships
from .version import VERSION

WRITER_VERSION = "sistela-vfp-clone-1"
STATUS = "EXPERIMENTAL"
WARNINGS = ["Naudokite tik bandomai SISTELA sąmatai.",
            "Original identifiers preserved: import only in an isolated test context.",
            "Generated DBFs have not been accepted in real SISTELA. No recalculation is assumed."]


class DbfExportBlocked(ValueError):
    def __init__(self, errors):
        self.errors = errors if isinstance(errors, list) else [errors]
        super().__init__("; ".join(self.errors))


def encode_field(field, value):
    try:
        if field.type == "C":
            if not isinstance(value, str) or "\0" in value or value.endswith(" "):
                raise ValueError("Text must be normalized without null/trailing padding")
            encoded = value.encode("cp1257", errors="strict")
        elif field.type == "N":
            if value is None:
                return b" " * field.length
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError("Only finite Decimal numeric values are accepted")
            with localcontext() as context:
                context.prec = max(50, field.length * 2)
                quantized = value.quantize(Decimal(1).scaleb(-field.decimals))
            if quantized != value:
                raise ValueError("Numeric scale loss is forbidden")
            encoded = format(quantized, f".{field.decimals}f").encode("ascii")
        elif field.type == "D":
            if value is None:
                return b" " * field.length
            if type(value) is not date:
                raise ValueError("Expected a date")
            encoded = f"{value.year:04d}{value.month:02d}{value.day:02d}".encode("ascii")
        else:
            raise ValueError("Unsupported field type")
        if len(encoded) > field.length:
            raise ValueError("Encoded value exceeds field width")
        return encoded.rjust(field.length, b" ") if field.type == "N" else encoded.ljust(field.length, b" ")
    except (UnicodeError, ValueError, InvalidOperation) as exc:
        raise DbfExportBlocked(f"{field.name}: {type(exc).__name__}: value/type/width/scale invalid") from exc


def serialize_table(table):
    header = bytearray(table.header)
    struct.pack_into("<I", header, 4, len(table.records))
    output = bytearray(header)
    expected_names = {f.name for f in table.fields}
    for number, row in enumerate(table.records, 1):
        if set(row.values) != expected_names:
            raise DbfExportBlocked(f"{table.filename} record {number}: missing or extra fields")
        output.extend(b"*" if row.deleted else b" ")
        for field in table.fields:
            output.extend(encode_field(field, row.values[field.name]))
    output.extend(table.trailer)
    data = bytes(output)
    # Re-parse our output; schema/header/record consistency is checked before publication.
    reparsed = parse_table(table.filename, data)
    if reparsed.fields != table.fields or reparsed.records != table.records:
        raise DbfExportBlocked(f"{table.filename}: serialization did not preserve normalized records")
    return data


@dataclass
class DbfExportResult:
    destination: str
    generated_filenames: list[str]
    record_counts: dict[str, int]
    validation: dict
    warnings: list[str]
    hashes: dict[str, str]
    mode: str
    status: str = STATUS


def _safe_root(root):
    # Reject reparse points throughout the existing ancestry, not just the final folder.
    for part in (root, *root.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise DbfExportBlocked("Export path contains a symlink/junction")
    return root.resolve()


class SistelaDbfExporter:
    def __init__(self, data_directory: Path):
        # Public API accepts application data only; export destinations are generated children.
        self.root = Path(data_directory).absolute() / "exports"

    def export_clone(self, files, destination, *, mutation=None):
        tables = read_archive(files)
        errors = validate_relationships(tables)
        if errors:
            raise DbfExportBlocked(errors)
        baseline = copy.deepcopy(tables)
        changes = []
        mode = "ROUND_TRIP_CLONE"
        if mutation is not None:
            mode = "CONTROLLED_TEXT_MUTATION"
            if set(mutation) != {"record", "field", "value"} or mutation["field"] != "PAVADIN":
                raise DbfExportBlocked("QUANTITY_DEPENDENCIES_UNKNOWN: only dd GRUP=10 PAVADIN mutation is permitted")
            number = mutation["record"]
            if type(number) is not int or not 1 <= number <= len(tables["dd"].records):
                raise DbfExportBlocked("Invalid physical dd record number")
            row = tables["dd"].records[number - 1]
            if row.deleted or row.values["GRUP"] != 10:
                raise DbfExportBlocked("Mutation requires an active dd GRUP=10 header")
            previous = row.values["PAVADIN"]
            value = mutation["value"]
            if not isinstance(value, str) or not value.strip() or value == previous:
                raise DbfExportBlocked("Mutation must change exactly one nonempty description")
            row.values["PAVADIN"] = value
            changes.append({"file": tables["dd"].filename, "record": number, "field": "PAVADIN",
                            "before": previous, "after": value})
        encoded = {t.filename: serialize_table(t) for t in tables.values()}
        output = read_archive(encoded)
        errors = validate_relationships(output)
        comparison = compare_archives(baseline, output)
        expected = [f"dd record {mutation['record']} field PAVADIN: value differs"] if mutation else []
        if errors or comparison["differences"] != expected:
            raise DbfExportBlocked(errors + ["Unexpected round-trip differences"])
        # Validate the entire archive in memory before creating even the staging directory.
        name = str(destination)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", name):
            raise DbfExportBlocked("Destination must be a new export folder name, not a path")
        root = _safe_root(self.root)
        final = root / name
        if final.exists() or final.is_symlink():
            raise DbfExportBlocked("Destination already exists; never overwrite an archive")
        root.mkdir(parents=True, exist_ok=True)
        result = DbfExportResult(str(final), [tables[r].filename for r in ROLES],
            {t.filename: len(t.records) for t in tables.values()},
            {"structural": "PASS", "relationships": "PASS", "comparison": comparison,
             "real_sistela": "UNVERIFIED", "project_export": "BLOCKED"},
            list(WARNINGS), {name: sha256(data).hexdigest() for name, data in encoded.items()}, mode)
        manifest = asdict(result) | {"application_version": VERSION, "writer_version": WRITER_VERSION,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": None, "project_name": None, "source_archive": "provided six-file archive",
            "source_hashes": {t.filename: t.checksum for t in baseline.values()},
            "changes": changes, "header_policy": "preserve original opaque metadata/date/LDID"}
        staging = Path(tempfile.mkdtemp(prefix=".dbf-staging-", dir=root))
        try:
            for filename, data in encoded.items():
                (staging / filename).write_bytes(data)
            (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            # Same-volume atomic publication; Windows rename never replaces an existing directory.
            if final.exists():
                raise DbfExportBlocked("Destination created concurrently")
            staging.rename(final)
        finally:
            if staging.exists():
                shutil.rmtree(staging)  # Only our newly created, private staging directory.
        return result

    def export_project(self, session, project_id, destination):
        from .dbf_project import project_export_plan
        plan = project_export_plan(session, project_id)
        raise DbfExportBlocked(plan["blockers"])
