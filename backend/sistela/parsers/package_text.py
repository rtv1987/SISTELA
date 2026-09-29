"""Lossless lexical analysis, NOT a claim to understand SISTELA's package grammar."""
import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class PackageTextLine:
    number: int
    raw: str
    ending: str
    tab_cells: list[str]
    code_candidates: list[str]
    kind: str


@dataclass(frozen=True)
class PackageTextReport:
    sha256: str
    encoding: str
    byte_count: int
    grammar_status: str
    text: str
    lines: list[PackageTextLine]
    warnings: list[str]

    def to_dict(self):
        return asdict(self)


class PackageTextParser:
    MAX_BYTES = 5 * 1024 * 1024

    def parse_bytes(self, data: bytes, *, encoding: str = "utf-8-sig") -> PackageTextReport:
        if len(data) > self.MAX_BYTES:
            raise ValueError("Package analysis limit: 5 MB")
        if encoding not in {"utf-8", "utf-8-sig", "utf-16", "cp1257", "cp1252"}:
            raise ValueError("Unsupported encoding; select an explicit supported encoding")
        try:
            text = data.decode(encoding, errors="strict")
        except UnicodeError as exc:
            raise ValueError("Cannot decode text strictly; choose the actual source encoding") from exc
        if "\0" in text:
            raise ValueError("Binary/NUL content is not supported")
        lines = []
        for number, part in enumerate(text.splitlines(keepends=True), 1):
            raw = part.rstrip("\r\n")
            ending = part[len(raw):]
            lines.append(PackageTextLine(
                number, raw, ending, raw.split("\t"),
                re.findall(r"(?<![\w-])N\d+-\d+(?:-\d+)*(?![\w-])", raw),
                "blank" if not raw.strip() else "uninterpreted",
            ))
        return PackageTextReport(hashlib.sha256(data).hexdigest(), encoding, len(data),
                                 "UNKNOWN", text, lines,
                                 ["No authentic package grammar has been verified.",
                                  "Code-shaped tokens are lexical candidates, not confirmed normative codes."])

    def parse(self, path: Path, *, encoding: str = "utf-8-sig") -> PackageTextReport:
        with path.open("rb") as source:
            data = source.read(self.MAX_BYTES + 1)
        return self.parse_bytes(data, encoding=encoding)
