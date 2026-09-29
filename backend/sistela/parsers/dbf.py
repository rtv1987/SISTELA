"""Read-only DBF introspection; never infer semantics from a filename."""

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from dbfread import DBF, FieldParser


class DbfReadError(ValueError):
    pass


class DecimalFieldParser(FieldParser):
    def parseN(self, field, data):
        value = data.strip().strip(b"\0")
        if not value:
            return None
        try:
            number = Decimal(value.decode("ascii"))
        except (UnicodeDecodeError, InvalidOperation) as exc:
            raise DbfReadError(f"Invalid numeric field: {field.name}") from exc
        if not number.is_finite():
            raise DbfReadError(f"Non-finite numeric field: {field.name}")
        return number

    parseF = parseN


@dataclass(frozen=True)
class DbfField:
    name: str
    type: str
    length: int
    decimals: int


@dataclass
class DbfSnapshot:
    filename: str
    checksum: str
    version: int
    language_driver: int
    declared_encoding: str
    selected_encoding: str
    declared_records: int
    deleted_records: int
    fields: list[DbfField]
    records: list[dict]

    def schema(self):
        return [asdict(field) for field in self.fields]


def read_dbf(path: Path, *, encoding: str) -> DbfSnapshot:
    """Encoding is mandatory: this archive's LDID is demonstrably misleading."""
    before = path.read_bytes()
    if len(before) < 32:
        raise DbfReadError("Truncated DBF header")
    count = int.from_bytes(before[4:8], "little")
    header_length = int.from_bytes(before[8:10], "little")
    record_length = int.from_bytes(before[10:12], "little")
    if header_length < 33 or record_length < 1:
        raise DbfReadError("Invalid DBF lengths")
    if len(before) < header_length + count * record_length:
        raise DbfReadError("Truncated DBF records")
    try:
        declared = DBF(str(path), load=False).encoding
        table = DBF(
            str(path),
            encoding=encoding,
            char_decode_errors="strict",
            parserclass=DecimalFieldParser,
            load=False,
        )
        records = list(table)
        deleted = len(list(table.deleted))
        fields = [DbfField(f.name, f.type, f.length, f.decimal_count) for f in table.fields]
    except (UnicodeError, LookupError, ValueError, OSError) as exc:
        # Do not include record contents from a library exception in user-facing errors.
        raise DbfReadError("DBF decoding failed; check encoding, schema and memo files") from exc
    if len(records) + deleted != count:
        raise DbfReadError("DBF record count does not match header")
    checksum = sha256(before).hexdigest()
    if sha256(path.read_bytes()).hexdigest() != checksum:
        raise DbfReadError("Source changed during inspection")
    return DbfSnapshot(
        path.name,
        checksum,
        before[0],
        before[29],
        declared,
        encoding,
        count,
        deleted,
        fields,
        records,
    )
