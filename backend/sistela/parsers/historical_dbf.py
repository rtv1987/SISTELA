"""Read-only reconstruction of the documented sd/dd profile. No catalogue claims."""

import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import PureWindowsPath

from .common import normalize_text, normalize_unit
from .dbf import DbfReadError, DbfSnapshot

KEY = (
    "KOMPLEKSAS",
    "OBJEKTAS",
    "RANGOVAS",
    "SAMATA",
    "SKYRIUS",
    "SUSDARB1",
    "SAM_EILUTE",
    "DET_EILUTE",
)
ESTIMATE_KEY = KEY[:4]
SYSTEM_NAMES = {
    "apsaugine signalizacija": "AS",
    "gaisro aptikimo ir signalizavimo sistema": "GSS",
    "elektroniniai rysiai": "ER",
}
VERSION = "historical-sd-dd-1"


def detect_archive(files: dict[str, bytes]):
    roles, suffixes = {}, set()
    if not 3 <= len(files) <= 6:
        raise DbfReadError(
            "Pasirinkite vieno archyvo sd, dd, nd ir, jei yra, pd, td, od DBF failus."
        )
    for name, data in files.items():
        if PureWindowsPath(name).name != name:
            raise DbfReadError("Importui naudokite failo vardą be katalogo kelio.")
        name = PureWindowsPath(name).name
        stem = name.lower()
        role = stem[:2]
        if (
            role not in {"sd", "dd", "nd", "pd", "td", "od"}
            or not stem.endswith(".dbf")
            or role in roles
        ):
            raise DbfReadError("Neatpažintas arba pasikartojantis DBF failas.")
        if not data or len(data) > 25 * 1024 * 1024:
            raise DbfReadError("DBF failas tuščias arba viršija 25 MB.")
        suffixes.add(stem[2:-4])
        roles[role] = {"name": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    if len(suffixes) != 1 or not {"sd", "dd", "nd"} <= roles.keys():
        raise DbfReadError(
            "Būtinas vienas suderintas sd/dd/nd rinkinys su vienodu failų vardų sufiksu."
        )
    identity = hashlib.sha256(
        json.dumps({k: roles[k]["sha256"] for k in ("sd", "dd", "nd")}, sort_keys=True).encode()
    ).hexdigest()
    return roles, identity


def key(row, fields=KEY):
    return tuple(str(row.get(k)) if row.get(k) is not None else None for k in fields)


def refs(snapshot):
    numbers = snapshot.record_numbers or list(range(1, len(snapshot.records) + 1))
    return list(zip(numbers, snapshot.records, strict=True))


def reconstruct(tables: dict[str, DbfSnapshot]):
    required = {
        "sd": set(KEY) | {"IKAINIS", "KIEKIS"},
        "dd": set(KEY) | {"GRUP", "IKAINIS", "KIEKIS", "PAVADIN", "MATO_PAV"},
        "nd": set(ESTIMATE_KEY) | {"SKYRIUS", "POZ", "PAVADIN"},
    }
    for role, fields in required.items():
        if not fields <= {f.name for f in tables[role].fields}:
            raise DbfReadError(f"Nepalaikoma {role} schema: trūksta privalomų laukų.")
        numeric = (fields & set(KEY[1:])) | (fields & {"GRUP", "POZ", "KIEKIS"})
        for row in tables[role].records:
            if any(
                row.get(name) is not None and not isinstance(row[name], Decimal) for name in numeric
            ):
                raise DbfReadError(f"Nepalaikoma {role} schema: skaitinių laukų tipai nesutampa.")
    sd, dd, nd = (refs(tables[role]) for role in ("sd", "dd", "nd"))
    if len(sd) > 10000 or len(dd) > 100000:
        raise DbfReadError("Archyvas viršija istorijos importo eilučių limitą.")
    parents = defaultdict(list)
    for number, row in sd:
        parents[key(row)].append((number, row))
    headers = [(number, row) for number, row in dd if row["GRUP"] == 10]
    header_counts = Counter(key(r) for _, r in headers)
    estimates, lines, warnings = {}, [], []

    def reference(role, number, row):
        return {
            "file": tables[role].filename,
            "sha256": tables[role].checksum,
            "record": number,
            "fields": json.loads(json.dumps(row, default=str)),
        }

    for number, row in headers:
        ek = key(row, ESTIMATE_KEY)
        names = [
            (n, r)
            for n, r in nd
            if key(r, ESTIMATE_KEY) == ek and r["POZ"] == 3 and r["SKYRIUS"] is None
        ]
        sections = [
            (n, r)
            for n, r in nd
            if key(r, ESTIMATE_KEY) == ek and r["POZ"] == 4 and r["SKYRIUS"] == row["SKYRIUS"]
        ]
        objects = [
            (n, r)
            for n, r in nd
            if key(r, ESTIMATE_KEY[:2]) == ek[:2] and r["POZ"] == 2 and r["SAMATA"] is None
        ]
        section = str(sections[0][1]["PAVADIN"]).strip() if len(sections) == 1 else ""
        if ek not in estimates:
            name = (
                str(names[0][1]["PAVADIN"]).strip()
                if len(names) == 1
                else f"Sąmata {row['SAMATA']}"
            )
            source_date = str(names[0][1].get("KODAT") or "") or None if len(names) == 1 else None
            estimates[ek] = {
                "external_key": dict(zip(ESTIMATE_KEY, ek, strict=True)),
                "name": name,
                "project_name": str(objects[0][1]["PAVADIN"]).strip()
                if len(objects) == 1
                else f"Objektas {row['OBJEKTAS']}",
                "system_type": SYSTEM_NAMES.get(normalize_text(name), ""),
                "system_evidence": "INFERENCE: estimate name alias; verify on confirmation",
                "source_date": source_date,
                "source_reference": {
                    "estimate": [reference("nd", n, r) for n, r in names],
                    "project": [reference("nd", n, r) for n, r in objects],
                },
            }
        matches = parents[key(row)]
        consistent = (
            len(matches) == 1
            and matches[0][1]["IKAINIS"] == row["IKAINIS"]
            and matches[0][1]["KIEKIS"] == row["KIEKIS"]
        )
        relationship = "DERIVED" if consistent else "DIRECT" if not matches else "AMBIGUOUS"
        if (
            header_counts[key(row)] != 1
            or len(names) != 1
            or len(sections) != 1
            or any(v is None for v in ek)
        ):
            relationship = "AMBIGUOUS"
        label = normalize_text(section)
        kind = (
            "Work"
            if label in {"darbai", "montavimo darbai"}
            else "Material"
            if label == "medziagos"
            else "Other"
        )
        if kind == "Other":
            relationship = "AMBIGUOUS"
        description, code = str(row["PAVADIN"]).strip(), str(row["IKAINIS"]).strip()
        unit = normalize_unit(str(row["MATO_PAV"]))
        if not description or not code or not unit or row["KIEKIS"] is None or row["KIEKIS"] < 0:
            relationship = "AMBIGUOUS"
        if relationship == "AMBIGUOUS":
            warnings.append(
                {
                    "code": "AMBIGUOUS_LINE",
                    "file": tables["dd"].filename,
                    "record": number,
                    "message": "Neaiški pozicijos, sąmatos, skyriaus jungtis arba trūksta reikšmių.",
                }
            )
        lines.append(
            {
                "estimate_key": ek,
                "external_key": dict(zip(KEY, key(row), strict=True)),
                "line_type": kind,
                "description": description,
                "normalized_description": normalize_text(description),
                "sistela_code": code,
                "unit": unit,
                "quantity": row["KIEKIS"],
                "historical_price": row.get("KAINA"),
                "section_name": section,
                "system_type": estimates[ek]["system_type"],
                "evidence_type": relationship,
                "confidence": "0.45" if relationship == "AMBIGUOUS" else "0.90",
                "status": "NOT_APPLICABLE" if kind == "Material" else "CANDIDATE",
                "evidence": {
                    "description_kind": "historical_output_not_catalogue",
                    "header": reference("dd", number, row),
                    "parents": [reference("sd", n, r) for n, r in matches],
                    "section": [reference("nd", n, r) for n, r in sections],
                    "rule": "sd/dd eight-field key + equal IKAINIS/KIEKIS; dd GRUP=10; nd key cardinality checked",
                },
            }
        )
    for number, row in sd:
        if key(row) not in header_counts:
            warnings.append(
                {
                    "code": "MISSING_HEADER",
                    "record": number,
                    "file": tables["sd"].filename,
                    "message": "sd pozicija neturi dd GRUP=10 aprašymo; kandidatas nesukurtas.",
                }
            )
    if not lines:
        raise DbfReadError("Nerasta dd GRUP=10 pozicijų.")
    return list(estimates.items()), lines, warnings
