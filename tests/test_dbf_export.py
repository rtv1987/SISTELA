import copy
import hashlib
import io
import json
import struct
import zipfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_workflow import confirm, line, project

from sistela.api import create_app
from sistela.db import make_engine, migrate
from sistela.dbf_archive import (
    ROLES,
    analyze_archive,
    compare_archives,
    parse_table,
    read_archive,
    read_directory,
    validate_relationships,
)
from sistela.dbf_export import DbfExportBlocked, SistelaDbfExporter, encode_field, serialize_table
from sistela.dbf_project import allocate_identifiers
from sistela.parsers.dbf import DbfField, DbfReadError, read_dbf


@pytest.fixture
def golden(source_file):
    return {f"{r}25-04-14.dbf": source_file(f"{r}25-04-14.dbf").read_bytes() for r in ROLES}


@pytest.fixture
def client(tmp_path):
    migrate(tmp_path)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as value:
        yield value


def test_all_six_golden_tables_normalized_roundtrip_and_original_hashes(golden, source_file, tmp_path):
    expected = json.loads((Path(__file__).parents[1] / "docs/sistela-dbf-golden-schema.json").read_text(encoding="utf-8"))
    before = read_archive(golden)
    result = SistelaDbfExporter(tmp_path).export_clone(golden, "TEST_A_CLONE")
    after = read_directory(Path(result.destination))
    assert compare_archives(before, after)["status"] == "SAME"
    assert not validate_relationships(after)
    assert result.validation["real_sistela"] == "UNVERIFIED"
    assert result.status == "EXPERIMENTAL"
    for role in ROLES:
        old, new = before[role], after[role]
        assert [vars(f) for f in new.fields] == expected[role]["fields"]
        assert old.records == new.records and old.fields == new.fields
        assert old.header == new.header and old.trailer == new.trailer
        independent = read_dbf(Path(result.destination) / new.filename, encoding="cp1257")
        assert independent.records == new.active  # Independent dbfread implementation.
        assert hashlib.sha256(source_file(old.filename).read_bytes()).hexdigest() == expected[role]["sha256"]
        assert result.hashes[new.filename] == new.checksum
    assert len(after["od"].records) == 0 and len(after["od"].header) == 808
    assert after["od"].trailer == b""
    manifest = json.loads((Path(result.destination) / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["changes"] == [] and manifest["mode"] == "ROUND_TRIP_CLONE"
    assert manifest["writer_version"] and manifest["application_version"]
    assert manifest["hashes"] == result.hashes
    assert len(after["sd"].active) == 104
    assert sum(r["POZ"] == 3 for r in after["nd"].active) == 3


def test_controlled_one_text_change_keeps_all_numbers_keys_and_relations(golden, tmp_path):
    old = read_archive(golden)
    result = SistelaDbfExporter(tmp_path).export_clone(golden, "TEST_B_ONE_CHANGE",
        mutation={"record": 174, "field": "PAVADIN", "value": old["dd"].records[173].values["PAVADIN"] + " [TEST_B]"})
    current = read_directory(Path(result.destination))
    compare = compare_archives(old, current)
    assert compare["differences"] == ["dd record 174 field PAVADIN: value differs"]
    assert not compare["right_relationship_errors"]
    for role in ROLES:
        for left, right in zip(old[role].records, current[role].records, strict=True):
            assert {k: v for k, v in left.values.items() if not isinstance(v, str)} == {k: v for k, v in right.values.items() if not isinstance(v, str)}


def test_quantity_mutation_is_blocked_without_any_output(golden, tmp_path):
    with pytest.raises(DbfExportBlocked, match="QUANTITY_DEPENDENCIES_UNKNOWN"):
        SistelaDbfExporter(tmp_path).export_clone(golden, "NO_OUTPUT", mutation={"record":174,"field":"KIEKIS","value":"116"})
    assert not (tmp_path / "exports").exists()


@pytest.mark.parametrize("text", ["Ą Č Ę Ė Į Š Ų Ū Ž", "ą č ę ė į š ų ū ž", " D25-04-14"])
def test_cp1257_lithuanian_and_leading_spaces(golden, text):
    table = read_archive(golden)["dd"]
    table.records[0].values["PAVADIN"] = text
    assert parse_table(table.filename, serialize_table(table)).records[0].values["PAVADIN"] == text


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("-0.000001"), Decimal("999999.999999"), None])
def test_decimal_exact_serialization(value):
    field = DbfField("KIEKIS", "N", 13, 6)
    raw = encode_field(field, value)
    assert (Decimal(raw.decode().strip()) if raw.strip() else None) == value


@pytest.mark.parametrize("field,value", [
    (DbfField("KIEKIS", "N", 13, 6), 0.1),
    (DbfField("KIEKIS", "N", 13, 6), Decimal("0.0000001")),
    (DbfField("KIEKIS", "N", 13, 6), Decimal("1000000.000000")),
    (DbfField("KIEKIS", "N", 13, 6), Decimal("NaN")),
    (DbfField("PAVADIN", "C", 2, 0), "abc"),
    (DbfField("PAVADIN", "C", 240, 0), "🚫"),
])
def test_writer_rejects_lossy_numeric_or_text_values(field, value):
    with pytest.raises(DbfExportBlocked):
        encode_field(field, value)


def test_deleted_flags_dates_blanks_and_header_date_preserved(golden):
    table = read_archive(golden)["nd"]
    table.records[0].deleted = True
    current = parse_table(table.filename, serialize_table(table))
    assert current.records == table.records and current.header == table.header
    assert current.records[0].values["SAMATA"] is None
    assert current.records[1].values["KODAT"].isoformat() == "2026-08-21"


@pytest.mark.parametrize("change", ["dangling_dd", "duplicate_sd", "quantity", "missing_section", "duplicate_estimate"])
def test_proven_relationship_errors_block_export(golden, tmp_path, change):
    tables = read_archive(golden)
    if change == "dangling_dd":
        tables["dd"].records[0].values["SAM_EILUTE"] = Decimal(9999)
    elif change == "duplicate_sd":
        tables["sd"].records.append(copy.deepcopy(tables["sd"].records[0]))
    elif change == "quantity":
        tables["sd"].records[0].values["KIEKIS"] += 1
    elif change == "missing_section":
        tables["nd"].records[2].deleted = True
    else:
        tables["nd"].records.append(copy.deepcopy(tables["nd"].records[1]))
    assert validate_relationships(tables)
    with pytest.raises(DbfExportBlocked):
        SistelaDbfExporter(tmp_path).export_clone({t.filename: serialize_table(t) for t in tables.values()}, "INVALID")
    assert not (tmp_path / "exports").exists()


@pytest.mark.parametrize("destination", ["../golden", "C:\\SISTELA", "/absolute", "a/b", "dd25-04-14.dbf"])
def test_export_destination_cannot_escape_owned_exports(golden, tmp_path, destination):
    with pytest.raises(DbfExportBlocked):
        SistelaDbfExporter(tmp_path).export_clone(golden, destination)


def test_never_overwrite_even_existing_empty_destination(golden, tmp_path):
    target = tmp_path / "exports/EXISTS"
    target.mkdir(parents=True)
    with pytest.raises(DbfExportBlocked, match="already exists"):
        SistelaDbfExporter(tmp_path).export_clone(golden, "EXISTS")
    assert list(target.iterdir()) == []


def test_comparison_reports_exact_record_field_and_schema(golden):
    left, right = read_archive(golden), read_archive(golden)
    right["dd"].records[0].values["KIEKIS"] += 1
    right["dd"].fields = (replace(right["dd"].fields[0], length=11), *right["dd"].fields[1:])
    differences = compare_archives(left, right)["differences"]
    assert "dd record 1 field KIEKIS: value differs" in differences
    assert any("field position 1" in d and "KOMPLEKSAS" in d for d in differences)


@pytest.mark.parametrize("problem", ["missing_od", "bad_version", "truncated", "unsafe_filename", "wrong_ldid"])
def test_invalid_archive_profile_fails_closed(golden, problem):
    files = dict(golden)
    if problem == "missing_od":
        del files["od25-04-14.dbf"]
    elif problem == "unsafe_filename":
        files["dd:unsafe.dbf"] = files.pop("dd25-04-14.dbf")
    else:
        data = bytearray(files["dd25-04-14.dbf"])
        if problem == "bad_version":
            data[0] = 3
        elif problem == "wrong_ldid":
            data[29] = 0
        else:
            data = data[:-15]
        files["dd25-04-14.dbf"] = bytes(data)
    with pytest.raises(DbfReadError):
        read_archive(files)


def test_analysis_classifies_every_field_conservatively(golden):
    result = analyze_archive(read_archive(golden))
    assert sum(len(t["fields"]) for t in result.values()) == 232
    assert all(f["classification"] in {"INPUT", "UNKNOWN"} for t in result.values() for f in t["fields"])
    assert next(f for f in result["dd"]["fields"] if f["name"] == "VERTE")["classification"] == "UNKNOWN"


def test_deterministic_identifier_proposals_and_collision_check():
    sections = [("materials", ["a", "b"]), ("works", ["c"])]
    first = allocate_identifiers("project", sections)
    assert first == allocate_identifiers("project", sections)
    assert first[2]["SKYRIUS"] == 2 and first[2]["SAM_EILUTE"] == 1
    assert len(first[0]["KOMPLEKSAS"]) == 10
    with pytest.raises(DbfExportBlocked, match="COLLISION"):
        allocate_identifiers("project", sections, [first[0]["KOMPLEKSAS"]])
    with pytest.raises(DbfExportBlocked, match="DUPLICATE"):
        allocate_identifiers("project", [("section", ["a", "a"])])


def test_project_preparation_preserves_concepts_materials_and_explicit_target(client, tmp_path):
    pid = project(client)
    material = line(client, pid, line_type="Material", project_description="Cable", output_description="Output cable", unit="m", quantity="650")
    work = line(client, pid, unit="m", quantity="650")
    response = client.post(f"/projects/{pid}/lines/{work['id']}/review", json={"version":work['version'],"action":"convert","target_unit":"100m"})
    assert response.status_code == 200
    confirm(client, response.json(), code="TEST-100M", unit="100m")
    plan = client.get(f"/projects/{pid}/dbf/plan").json()
    assert plan["status"] == "BLOCKED" and len(plan["rows"]) == 2
    row = next(r for r in plan["rows"] if r["source_line_id"] == work["id"])
    assert Decimal(row["target_quantity"]) == Decimal("6.5") and row["source_quantity"] == "650"
    assert row["target_unit"] == "100m" and row["conversion_valid"]
    assert row["sistela_code"] == "TEST-100M"
    assert next(r for r in plan["rows"] if r["source_line_id"] == material["id"])["output_description"] == "Output cable"
    assert len({r["SKYRIUS"] for r in plan["proposed_identifiers"]}) == 2
    assert client.post(f"/projects/{pid}/export/dbf").status_code == 409
    from sqlalchemy.orm import Session
    engine = make_engine(tmp_path)
    with Session(engine) as session, pytest.raises(DbfExportBlocked, match="CALCULATED_FIELDS_UNKNOWN"):
        SistelaDbfExporter(tmp_path).export_project(session, pid, "PROJECT")
    engine.dispose()
    assert not (tmp_path / "exports").exists()


def test_project_plan_reports_unconfirmed_work(client):
    pid = project(client)
    line(client, pid)
    assert any("UNCONFIRMED" in b or "MAPPING" in b or "SISTELA_CODE" in b for b in client.get(f"/projects/{pid}/dbf/plan").json()["blockers"])


def test_clone_download_six_dbfs_and_manifest_no_project_export(client, golden):
    response = client.post("/dbf/clone", files=[("files", (n, b)) for n, b in golden.items()])
    assert response.status_code == 200, response.text[:100] if response.status_code != 200 else ""
    assert response.headers["x-sistela-export-status"] == "EXPERIMENTAL"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == set(golden) | {"manifest.json"}
        generated = read_archive({n: archive.read(n) for n in golden})
    assert compare_archives(read_archive(golden), generated)["status"] == "SAME"


def test_header_count_mismatch_is_rejected(golden):
    raw = bytearray(golden["dd25-04-14.dbf"])
    struct.pack_into("<I", raw, 4, 392)
    with pytest.raises(DbfReadError):
        parse_table("dd25-04-14.dbf", raw)
