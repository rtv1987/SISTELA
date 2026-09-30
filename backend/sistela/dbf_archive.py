"""Read-only physical archive model for a bounded FoxPro C/N/D profile.

Unlike the historical knowledge importer, keeps deleted rows and opaque header
metadata. Serialization lives in dbf_export, never in the importer.
"""
import re
import struct
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from .parsers.dbf import DbfField, DbfReadError
from .parsers.historical_dbf import ESTIMATE_KEY, KEY, detect_archive, key

ROLES = ("dd", "nd", "od", "pd", "sd", "td")


@dataclass
class ArchiveRecord:
    deleted: bool
    values: dict


@dataclass
class ArchiveTable:
    filename: str
    header: bytes
    fields: tuple[DbfField, ...]
    records: list[ArchiveRecord]
    trailer: bytes
    checksum: str

    @property
    def active(self):
        return [row.values for row in self.records if not row.deleted]


def parse_table(filename: str, data: bytes) -> ArchiveTable:
    if len(data) < 296 or data[0] != 0x30 or data[28] != 0 or data[29] != 3:
        raise DbfReadError(f"{filename}: unsupported FoxPro profile/version/flags/LDID")
    count, header_size, record_size = struct.unpack_from("<IHH", data, 4)
    if header_size < 328 or (header_size - 296) % 32 or count > 100000:
        raise DbfReadError(f"{filename}: invalid header/count")
    field_count = (header_size - 296) // 32
    if header_size > len(data) or header_size + count * record_size > len(data):
        raise DbfReadError(f"{filename}: truncated DBF")
    end = 32 + field_count * 32
    if data[end] != 13 or any(data[end + 1:header_size]):
        raise DbfReadError(f"{filename}: unsupported descriptor terminator/backlink")
    fields = []
    offset = 1
    for i in range(field_count):
        descriptor = data[32 + i * 32:64 + i * 32]
        try:
            name = descriptor[:11].split(b"\0")[0].decode("ascii")
            kind = chr(descriptor[11])
        except UnicodeError as exc:
            raise DbfReadError(f"{filename}: invalid field name") from exc
        width, scale = descriptor[16:18]
        if (not name or kind not in {"C", "N", "D"} or not width or descriptor[18]
                or (kind == "D" and (width != 8 or scale))
                or (kind == "C" and scale) or scale >= width
                or int.from_bytes(descriptor[12:16], "little") != offset):
            raise DbfReadError(f"{filename}.{name}: unsupported field descriptor")
        fields.append(DbfField(name, kind, width, scale))
        offset += width
    if offset != record_size or len({f.name for f in fields}) != len(fields):
        raise DbfReadError(f"{filename}: record length or duplicate fields")
    trailer = data[header_size + count * record_size:]
    if trailer not in (b"", b"\x1a"):
        raise DbfReadError(f"{filename}: unexpected trailing data")
    records = []
    for index in range(count):
        start = header_size + index * record_size
        if data[start:start + 1] not in (b" ", b"*"):
            raise DbfReadError(f"{filename}: invalid deleted flag at record {index + 1}")
        values, position = {}, start + 1
        for field in fields:
            raw = data[position:position + field.length]
            position += field.length
            try:
                if field.type == "C":
                    value = raw.rstrip(b" \0").decode("cp1257", errors="strict")
                elif field.type == "N":
                    value = Decimal(raw.strip().decode("ascii")) if raw.strip() else None
                    if value is not None and not value.is_finite():
                        raise ValueError("non-finite")
                else:
                    text = raw.decode("ascii")
                    value = date(int(text[:4]), int(text[4:6]), int(text[6:])) if text.strip() else None
            except (UnicodeError, ValueError, InvalidOperation) as exc:
                raise DbfReadError(f"{filename}: invalid {field.name} at record {index + 1}") from exc
            values[field.name] = value
        records.append(ArchiveRecord(data[start] == 42, values))
    return ArchiveTable(filename, data[:header_size], tuple(fields), records, trailer, sha256(data).hexdigest())


def read_archive(files: dict[str, bytes]) -> dict[str, ArchiveTable]:
    if any(not re.fullmatch(r"(?:dd|nd|od|pd|sd|td)[A-Za-z0-9_-]{1,80}\.dbf", name, re.IGNORECASE) for name in files):
        raise DbfReadError("Unsafe or unsupported archive filename")
    roles, _ = detect_archive(files)
    if set(roles) != set(ROLES):
        raise DbfReadError("Export requires all six DBF tables, including empty OD")
    return {role: parse_table(roles[role]["name"], files[roles[role]["name"]]) for role in ROLES}


def read_directory(directory: Path):
    return read_archive({path.name: path.read_bytes() for path in directory.glob("*.dbf")})


def validate_relationships(tables):
    """Only the established sd/dd and nd relationships; no invented pd/td keys."""
    errors = []
    if set(tables) != set(ROLES):
        return ["SIX_TABLES_REQUIRED"]
    required = {"sd": set(KEY) | {"IKAINIS", "KIEKIS"},
                "dd": set(KEY) | {"GRUP", "IKAINIS", "KIEKIS", "PAVADIN", "MATO_PAV"},
                "nd": set(ESTIMATE_KEY) | {"POZ", "SKYRIUS", "PAVADIN"}}
    for role, names in required.items():
        if not names <= {f.name for f in tables[role].fields}:
            errors.append(f"{role}: REQUIRED_FIELDS_MISSING")
    if errors:
        return errors
    sd, dd, nd = (tables[r].active for r in ("sd", "dd", "nd"))
    parents = Counter(key(r) for r in sd)
    headers = Counter(key(r) for r in dd if r["GRUP"] == 10)
    for label, counts in (("sd", parents), ("dd GRUP=10", headers)):
        if any(n != 1 for n in counts.values()):
            errors.append(f"{label}: DUPLICATE_POSITION_KEY")
    for number, row in enumerate(dd, 1):
        if parents[key(row)] != 1:
            errors.append(f"dd record {number}: DANGLING_OR_AMBIGUOUS_SD_KEY")
    estimates = Counter(key(r, ESTIMATE_KEY) for r in nd if r["POZ"] == 3 and r["SKYRIUS"] is None)
    sections = Counter(key(r, ESTIMATE_KEY + ("SKYRIUS",)) for r in nd if r["POZ"] == 4)
    objects = Counter(key(r, ESTIMATE_KEY[:2]) for r in nd if r["POZ"] == 2 and r["SAMATA"] is None)
    complexes = Counter(key(r, ("KOMPLEKSAS",)) for r in nd if r["POZ"] == 1)
    for label, counts in (("complex", complexes), ("object", objects), ("estimate", estimates), ("section", sections)):
        if any(n != 1 for n in counts.values()):
            errors.append(f"nd: DUPLICATE_{label.upper()}_KEY")
    for row in nd:
        if row["POZ"] in (2, 3, 4) and complexes[key(row, ("KOMPLEKSAS",))] != 1:
            errors.append("nd: DANGLING_COMPLEX")
        if row["POZ"] in (3, 4) and objects[key(row, ESTIMATE_KEY[:2])] != 1:
            errors.append("nd: DANGLING_OBJECT")
        if row["POZ"] == 4 and estimates[key(row, ESTIMATE_KEY)] != 1:
            errors.append("nd: DANGLING_ESTIMATE")
    by_key = {key(r): r for r in dd if r["GRUP"] == 10}
    for number, row in enumerate(sd, 1):
        match = by_key.get(key(row))
        if headers[key(row)] != 1 or match is None:
            errors.append(f"sd record {number}: MISSING_DD_HEADER")
        elif any(row[n] != match[n] for n in ("IKAINIS", "KIEKIS")):
            errors.append(f"sd record {number}: CODE_OR_QUANTITY_MISMATCH")
        if any(row[n] is None for n in KEY):
            errors.append(f"sd record {number}: MISSING_POSITION_KEY")
        if estimates[key(row, ESTIMATE_KEY)] != 1 or sections[key(row, ESTIMATE_KEY + ("SKYRIUS",))] != 1:
            errors.append(f"sd record {number}: MISSING_ND_HIERARCHY")
    return errors


def compare_archives(left, right):
    differences = []
    for role in ROLES:
        if role not in left or role not in right:
            differences.append(f"{role}: missing table")
            continue
        a, b = left[role], right[role]
        if a.fields != b.fields:
            differences.append(f"{role}: schema/order/type/width/scale differs")
            for index in range(max(len(a.fields), len(b.fields))):
                old = asdict(a.fields[index]) if index < len(a.fields) else None
                new = asdict(b.fields[index]) if index < len(b.fields) else None
                if old != new:
                    differences.append(f"{role} field position {index + 1}: {old} != {new}")
        # Dates may legitimately change. Other opaque metadata is kept observable.
        ah, bh = bytearray(a.header), bytearray(b.header)
        ah[1:8], bh[1:8] = b"\0" * 7, b"\0" * 7
        if ah != bh:
            differences.append(f"{role}: header/encoding/descriptor metadata differs")
        if a.filename != b.filename:
            differences.append(f"{role}: filename differs")
        if a.trailer != b.trailer:
            differences.append(f"{role}: EOF convention differs")
        if len(a.records) != len(b.records):
            differences.append(f"{role}: record count {len(a.records)} != {len(b.records)}")
        for i, (x, y) in enumerate(zip(a.records, b.records), 1):
            if x.deleted != y.deleted:
                differences.append(f"{role} record {i}: deleted flag differs")
            for name in sorted(x.values.keys() | y.values.keys()):
                if x.values.get(name) != y.values.get(name):
                    # No confidential values in routine command output.
                    differences.append(f"{role} record {i} field {name}: value differs")
    return {"status": "DIFFERENT" if differences else "SAME", "differences": differences,
            "left_relationship_errors": validate_relationships(left),
            "right_relationship_errors": validate_relationships(right)}


def field_category(role, name):
    if name in KEY or name == "SUSDARB2" or (role == "nd" and name in ("POZ", "PAVADIN")):
        return "INPUT"
    if role in ("sd", "dd") and name == "IKAINIS":
        return "INPUT"
    if role == "sd" and name == "KIEKIS":
        return "INPUT"
    # dd KIEKIS is INPUT only for GRUP=10; resource rows remain UNKNOWN.
    if role == "dd" and name in ("PAVADIN", "MATO_PAV", "KIEKIS"):
        return "UNKNOWN"
    return "UNKNOWN"


def analyze_archive(tables):
    return {role: {"filename": t.filename, "sha256": t.checksum,
        "header_hex": t.header[:32].hex(), "encoding": "cp1257", "ldid": t.header[29],
        "record_count": len(t.records), "deleted": sum(r.deleted for r in t.records),
        "trailer_hex": t.trailer.hex(), "field_order": [f.name for f in t.fields],
        "fields": [asdict(f) | {"classification": field_category(role, f.name),
            "conditional_input": "GRUP=10 only" if role == "dd" and f.name in ("PAVADIN", "MATO_PAV", "KIEKIS") else None,
            "required_for_clone": True, "required_for_new_project": "UNKNOWN"} for f in t.fields]}
        for role, t in tables.items()}
