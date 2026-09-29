import copy
import hashlib
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from sistela.api import create_app
from sistela.db import migrate
from sistela.parsers.dbf import DbfField, DbfReadError, DbfSnapshot
from sistela.parsers.historical_dbf import KEY, detect_archive, reconstruct
from sistela.units import convert_quantity, unit_compatibility


@pytest.fixture
def client(tmp_path):
    migrate(tmp_path)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as value:
        yield value


@pytest.fixture
def archive(source_file):
    return {
        role + "25-04-14.dbf": source_file(role + "25-04-14.dbf").read_bytes()
        for role in ("sd", "dd", "nd", "pd", "td", "od")
    }


def upload(client, archive):
    return client.post(
        "/history/imports",
        files=[("files", (name, data)) for name, data in archive.items()],
        data={"encoding": "cp1257"},
    )


def project_line(client, description="Detektorių montavimas", unit="vnt.", code=""):
    pid = client.post("/projects", json={"name": "Current", "system_type": "GSS"}).json()["id"]
    line = client.post(
        f"/projects/{pid}/lines",
        json={
            "project_description": description,
            "output_description": "Unchanged output",
            "system_type": "GSS",
            "line_type": "Work",
            "quantity": "650",
            "unit": unit,
            "work_price": "42",
            "sistela_code": code,
        },
    ).json()
    return f"/projects/{pid}/lines/{line['id']}", line


def review(client, row, status="CONFIRMED", **kwargs):
    return client.post(
        "/history/review",
        json={
            "items": [
                {"id": row["id"], "version": row["version"], "system_type": row["system_type"]}
            ],
            "status": status,
            **kwargs,
        },
    )


def synthetic_tables():
    base = dict(
        zip(
            KEY,
            [
                "C",
                Decimal(1),
                Decimal(0),
                Decimal(1),
                Decimal(2),
                Decimal(0),
                Decimal(1),
                Decimal(1),
            ],
            strict=True,
        )
    )
    header = dict(
        base,
        GRUP=Decimal(10),
        IKAINIS="TEST-1",
        KIEKIS=Decimal("2.5"),
        PAVADIN="Test work",
        MATO_PAV="VNT",
        KAINA=Decimal("12.3456"),
    )
    rows = {
        "sd": [dict(base, IKAINIS="TEST-1", KIEKIS=Decimal("2.5"))],
        "dd": [header],
        "nd": [
            dict(
                base,
                POZ=Decimal(3),
                SKYRIUS=None,
                PAVADIN="Gaisro aptikimo ir signalizavimo sistema",
            ),
            dict(base, POZ=Decimal(4), PAVADIN="Darbai"),
        ],
    }
    return {
        role: DbfSnapshot(
            role + ".dbf",
            role + "-hash",
            48,
            3,
            "cp1252",
            "cp1257",
            len(values),
            0,
            [DbfField(k, "C", 20, 0) for k in values[0]],
            values,
            list(range(1, len(values) + 1)),
        )
        for role, values in rows.items()
    }


def test_direct_derived_ambiguous_and_missing_parent():
    tables = synthetic_tables()
    _, lines, warnings = reconstruct(tables)
    assert not warnings and lines[0]["evidence_type"] == "DERIVED"
    assert lines[0]["evidence"]["header"]["record"] == 1
    tables["sd"].records = []
    tables["sd"].record_numbers = []
    assert reconstruct(tables)[1][0]["evidence_type"] == "DIRECT"
    tables = synthetic_tables()
    tables["sd"].records[0]["KIEKIS"] = Decimal(3)
    _, lines, warnings = reconstruct(tables)
    assert lines[0]["evidence_type"] == "AMBIGUOUS" and len(warnings) == 1
    tables = synthetic_tables()
    tables["dd"].records.append(copy.deepcopy(tables["dd"].records[0]))
    tables["dd"].record_numbers.append(2)
    assert all(row["evidence_type"] == "AMBIGUOUS" for row in reconstruct(tables)[1])


def test_missing_schema_is_rejected():
    tables = synthetic_tables()
    tables["sd"].fields = []
    with pytest.raises(DbfReadError, match="schema"):
        reconstruct(tables)


def test_wrong_numeric_types_are_controlled():
    tables = synthetic_tables()
    tables["dd"].records[0]["KIEKIS"] = "2.5"
    with pytest.raises(DbfReadError, match="schema"):
        reconstruct(tables)


@pytest.mark.fixtures
def test_physical_provenance_skips_deleted_record(source_file, tmp_path):
    from sistela.parsers.dbf import read_dbf

    original = source_file("dd25-04-14.dbf").read_bytes()
    data = bytearray(original)
    header_length = int.from_bytes(data[8:10], "little")
    data[header_length] = ord("*")
    copied = tmp_path / "deleted-copy.dbf"
    copied.write_bytes(data)
    parsed = read_dbf(copied, encoding="cp1257")
    assert parsed.deleted_records == 1 and parsed.record_numbers[0] == 2
    assert len(parsed.record_numbers) == len(parsed.records) == 390
    assert source_file("dd25-04-14.dbf").read_bytes() == original


@pytest.mark.parametrize(
    "source,target,status",
    [
        ("VNT", "vnt.", "IDENTICAL"),
        ("vnt", "VNT.", "IDENTICAL"),
        ("M", "m", "IDENTICAL"),
        ("KOMPL", "kompl.", "IDENTICAL"),
        ("100M", "100m", "IDENTICAL"),
        ("m", "100M", "CONVERTIBLE"),
        ("vnt.", "m", "INCOMPATIBLE"),
        ("", "m", "UNKNOWN"),
    ],
)
def test_unit_compatibility(source, target, status):
    assert unit_compatibility(source, target)["status"] == status


def test_conversion_is_explicit_exact_and_rejects_unsupported(client):
    assert convert_quantity(Decimal("650"), "m", "100M") == Decimal("6.50")
    assert convert_quantity(Decimal("6.5"), "100M", "m") == Decimal("650")
    with pytest.raises(ValueError):
        convert_quantity(Decimal("1"), "vnt.", "m")
    url, line = project_line(client, unit="m")
    result = client.post(
        "/units/convert", json={"quantity": "650", "source_unit": "m", "target_unit": "100M"}
    ).json()
    assert result["quantity"] == "6.50" and result["applied"] is False
    assert client.get(f"/projects/{line['project_id']}/lines").json()[0]["unit"] == "m"


@pytest.mark.fixtures
def test_real_archive_detection_import_idempotency_provenance(client, archive, source_file):
    roles, digest = detect_archive(archive)
    assert len(roles) == 6 and len(digest) == 64
    response = upload(client, archive)
    assert response.status_code == 200, response.text
    summary = response.json()
    assert (
        summary["line_count"] == 104
        and summary["work_count"] == 39
        and len(summary["estimates"]) == 3
    )
    assert summary["confirmed_count"] == 0 and summary["warning_count"] == 0
    assert {e["system_type"] for e in summary["estimates"]} == {"AS", "GSS", "ER"}
    again = upload(client, dict(reversed(list(archive.items())))).json()
    assert again["duplicate"] and again["id"] == summary["id"]
    assert len(client.get("/history/imports").json()) == 1
    all_lines = client.get("/history/lines").json()
    assert all_lines["total"] == 104
    works = [r for r in all_lines["items"] if r["line_type"] == "Work"]
    assert len({r["sistela_code"] for r in works}) == 34
    assert all(
        r["status"] == "CANDIDATE" and r["sistela_original_description"] == "" for r in works
    )
    assert all(
        r["status"] == "NOT_APPLICABLE" for r in all_lines["items"] if r["line_type"] == "Material"
    )
    evidence = client.get(f"/history/lines/{works[0]['id']}/evidence").json()
    assert evidence["evidence"]["header"]["file"] == "dd25-04-14.dbf"
    assert len(evidence["evidence"]["parents"]) == 1
    assert evidence["evidence"]["header"]["fields"]["IKAINIS"] == works[0]["sistela_code"]
    for name, data in archive.items():
        assert source_file(name).read_bytes() == data
        assert hashlib.sha256(data).hexdigest() == roles[name[:2]]["sha256"]


@pytest.mark.fixtures
def test_detection_rejects_mixed_missing_and_duplicate_roles(archive):
    for values in (
        {k: v for k, v in archive.items() if not k.startswith("sd")},
        {k.replace("sd25", "sd26"): v for k, v in archive.items()},
        dict(archive, sdOther=b"bad"),
    ):
        with pytest.raises(DbfReadError):
            detect_archive(values)


@pytest.mark.fixtures
def test_hash_mismatch_does_not_persist(client, archive, monkeypatch):
    import sistela.history

    original = sistela.history.read_dbf

    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        result.checksum = "wrong"
        return result

    monkeypatch.setattr(sistela.history, "read_dbf", corrupt)
    assert upload(client, archive).status_code == 422
    assert client.get("/history/imports").json() == []


@pytest.mark.fixtures
def test_review_rejection_ranking_units_and_prices(client, archive, tmp_path):
    assert upload(client, archive).status_code == 200
    row = client.get(
        "/history/lines", params={"system": "GSS", "code": "N50-270", "status": "CANDIDATE"}
    ).json()["items"][0]
    url, current = project_line(client, row["description"], row["unit"])
    suggestions = client.get(url + "/suggestions").json()
    historical = next(
        s
        for s in suggestions
        if s["origin"] == "historical" and s["sistela_code"] == row["sistela_code"]
    )
    assert historical["usage_count"] >= 1 and historical["project_count"] == 1
    assert historical["last_used_at"] is None
    assert historical["source_date"] == "2026-08-21"
    assert row["id"] in historical["evidence_ids"]
    assert review(client, row).status_code == 200
    assert review(client, row).status_code == 409  # stale version
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as reopened:
        assert reopened.get("/history/lines", params={"status": "CONFIRMED"}).json()["total"] == 1
    # Explicit current-project confirmation outranks the historical code.
    confirmed = client.post(
        url + "/mapping/confirm",
        json={
            "version": 1,
            "sistela_code": "USER-OVERRIDE",
            "normative_unit": row["unit"],
            "sistela_original_description": "Verified original",
        },
    ).json()
    assert client.get(url + "/suggestions").json()[0]["sistela_code"] == "USER-OVERRIDE"
    historical = next(
        s for s in client.get(url + "/suggestions").json() if s["origin"] == "historical"
    )
    applied = client.post(
        url + "/mapping/apply",
        json={"version": confirmed["version"], "mapping_id": historical["mapping_id"]},
    ).json()
    assert applied["work_price"] == "42" and applied["output_description"] == "Unchanged output"
    assert (
        applied["sistela_original_description"] == "" and applied["mapping_status"] == "suggested"
    )
    refreshed = client.get(f"/history/lines/{row['id']}/evidence").json()
    assert review(client, refreshed, "REJECTED").status_code == 200
    assert all(
        row["id"] not in s.get("evidence_ids", []) for s in client.get(url + "/suggestions").json()
    )
    cable = client.get("/history/lines", params={"system": "GSS", "code": "N50-210"}).json()[
        "items"
    ][0]
    other_url, _ = project_line(client, cable["description"], "m")
    incompatible = next(
        s for s in client.get(other_url + "/suggestions").json() if s["sistela_code"] == "N50-210"
    )
    assert (
        incompatible["unit_compatibility"]["status"] == "CONVERTIBLE"
        and not incompatible["compatible"]
    )
    assert (
        client.post(
            other_url + "/mapping/apply",
            json={"version": 1, "mapping_id": incompatible["mapping_id"]},
        ).status_code
        == 422
    )


@pytest.mark.fixtures
def test_aggregation_filters_and_bulk_review_atomicity(client, archive):
    upload(client, archive)
    rows = client.get("/history/lines", params={"system": "GSS", "code": "N50-333"}).json()["items"]
    assert len(rows) == 2
    url, _ = project_line(client, rows[0]["description"])
    aggregate = next(
        s for s in client.get(url + "/suggestions").json() if s["sistela_code"] == "N50-333"
    )
    assert aggregate["usage_count"] == 2 and aggregate["estimate_count"] == 1
    body = {
        "status": "CONFIRMED",
        "items": [{"id": r["id"], "version": r["version"]} for r in rows],
    }
    body["items"][1]["version"] = 99
    assert client.post("/history/review", json=body).status_code == 409
    assert client.get("/history/lines", params={"status": "CONFIRMED"}).json()["total"] == 0
    body["items"][1]["version"] = rows[1]["version"]
    assert client.post("/history/review", json=body).status_code == 200
    assert (
        client.get(
            "/history/lines", params={"status": "CONFIRMED", "search": rows[0]["description"][:10]}
        ).json()["total"]
        >= 1
    )


def test_ambiguous_bulk_is_blocked_single_requires_acknowledgement(client, tmp_path):
    from sqlalchemy.orm import Session

    from sistela.db import make_engine
    from sistela.models import HistoricalEstimate, HistoricalImport, HistoricalLine

    engine = make_engine(tmp_path)
    with Session(engine) as session:
        imported = HistoricalImport(
            source_hash="synthetic",
            source_reference="synthetic",
            source_files=[],
            encoding="cp1257",
            parser_version="test",
        )
        session.add(imported)
        session.flush()
        estimate = HistoricalEstimate(
            historical_import_id=imported.id,
            external_key={},
            name="Test",
            project_name="Test",
            system_type="GSS",
            system_evidence="test",
            source_reference={},
        )
        session.add(estimate)
        session.flush()
        row = HistoricalLine(
            historical_estimate_id=estimate.id,
            external_key={},
            line_type="Work",
            description="Test",
            normalized_description="test",
            sistela_code="TEST",
            unit="vnt.",
            section_name="Darbai",
            system_type="GSS",
            evidence_type="AMBIGUOUS",
            confidence=Decimal(".4"),
            evidence={},
        )
        session.add(row)
        session.commit()
        row_id = row.id
    engine.dispose()
    row = client.get(f"/history/lines/{row_id}/evidence").json()
    assert not row["bulk_eligible"]
    assert review(client, row).status_code == 422
    # Even an explicit acknowledgement cannot promote ambiguous evidence in a batch.
    with Session(engine) as session:
        original = session.get(HistoricalLine, row_id)
        other = HistoricalLine(
            **{
                column.name: getattr(original, column.name)
                for column in HistoricalLine.__table__.columns
                if column.name != "id"
            }
        )
        session.add(other)
        session.commit()
        other_id = other.id
    engine.dispose()
    assert (
        client.post(
            "/history/review",
            json={
                "status": "CONFIRMED",
                "acknowledge_ambiguity": True,
                "items": [{"id": row_id, "version": 1}, {"id": other_id, "version": 1}],
            },
        ).status_code
        == 422
    )
    assert review(client, row, acknowledge_ambiguity=True).status_code == 200


@pytest.mark.fixtures
@pytest.mark.parametrize("variant,method", [("upper", "normalized"), ("typo", "fuzzy")])
def test_historical_text_matching(client, archive, variant, method):
    upload(client, archive)
    row = client.get("/history/lines", params={"system": "GSS", "code": "N50-270"}).json()["items"][
        0
    ]
    text = row["description"].upper() if variant == "upper" else row["description"] + " darbai"
    url, _ = project_line(client, text, row["unit"])
    candidate = next(
        s for s in client.get(url + "/suggestions").json() if s["sistela_code"] == "N50-270"
    )
    assert candidate["method"] == method and candidate["compatible"]
