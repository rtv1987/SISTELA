from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from sistela.api import create_app
from sistela.db import make_engine, migrate
from sistela.models import EstimateLine, SourceDocument
from sistela.parsers.pdf import ParsedLine, PdfResult


@pytest.fixture
def client(tmp_path):
    migrate(tmp_path)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        yield client


def project(client):
    response = client.post("/projects", json={"name": "Test", "system_type": "GSS"})
    assert response.status_code == 201
    return response.json()["id"]


def test_project_and_line_persist_after_restart(client, tmp_path):
    pid = project(client)
    body = {
        "project_description": "Projekto tekstas",
        "output_description": "Siūlomas tekstas",
        "quantity": "0.123456",
        "work_price": "123456789.000001",
    }
    response = client.post(f"/projects/{pid}/lines", json=body)
    assert response.status_code == 201, response.text
    line = response.json()
    assert line["quantity"] == body["quantity"]
    assert line["work_price"] == body["work_price"]
    assert line["confidence"] is None
    # Same database, new app/session: no process-local dictionary as persistence.
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as reopened:
        assert reopened.get(f"/projects/{pid}").json()["name"] == "Test"
        assert reopened.get(f"/projects/{pid}/lines").json()[0]["id"] == line["id"]


def test_edit_conflict_and_float_validation(client):
    pid = project(client)
    values = {"project_description": "X", "output_description": "Y", "quantity": "2"}
    line = client.post(f"/projects/{pid}/lines", json=values).json()
    endpoint = f"/projects/{pid}/lines/{line['id']}"
    update = dict(values, version=1, quantity="3.5")
    assert client.put(endpoint, json=update).status_code == 200
    assert client.put(endpoint, json=update).status_code == 409
    assert client.post(f"/projects/{pid}/lines", json=dict(values, quantity=0.1)).status_code == 422
    assert (
        client.post(f"/projects/{pid}/lines", json=dict(values, quantity="NaN")).status_code == 422
    )


@pytest.mark.fixtures
def test_full_real_pdf_import(client, source_file, tmp_path, caplog):
    pid = project(client)
    data = source_file("2024-10-XX-TDP-GSS.pdf").read_bytes()
    endpoint = f"/projects/{pid}/imports/pdf"
    with caplog.at_level("INFO", logger="sistela"):
        response = client.post(
            endpoint, files={"file": ("../../project.pdf", data, "application/pdf")}
        )
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["status"] == "needs_review", run
    assert run["rows_detected"] == 21
    assert run["pages"] == [14]
    lines = client.get(f"/projects/{pid}/lines").json()
    assert len(lines) == 21
    assert all(
        line["mapping_status"] == "suggested" and line["confidence"] is None
        and line['sistela_code'] and line['review_data']['generated_code'] for line in lines
    )
    assert all(line["output_description"] == line["project_description"] for line in lines)
    assert len({line["sistela_code"] for line in lines}) == 21
    assert client.post(endpoint, files={"file": ("same.pdf", data)}).status_code == 409
    assert len(client.get(f"/projects/{pid}/lines").json()) == 21
    doc = client.get(f"/projects/{pid}/documents").json()[0]
    assert doc["filename"] == "project.pdf"
    assert (tmp_path / "documents" / (doc["checksum"] + ".pdf")).read_bytes() == data
    engine = make_engine(tmp_path)
    with Session(engine) as session:
        assert "MONTAVIMO DARBAI" in session.get(SourceDocument, doc["id"]).extracted_text
    engine.dispose()
    assert "import_start" in caplog.text and "import_end" in caplog.text
    assert "ULTRACELL" not in caplog.text
    assert "Zonų" not in caplog.text


def test_failed_import_is_audited(client):
    pid = project(client)
    response = client.post(f"/projects/{pid}/imports/pdf", files={"file": ("bad.pdf", b"SECRET")})
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert "INVALID_PDF" in response.json()["error_message"]
    assert "SECRET" not in response.json()["error_message"]
    assert client.get(f"/projects/{pid}/lines").json() == []
    assert len(client.get(f"/projects/{pid}/imports").json()) == 1


def test_import_transaction_rolls_back_partial_rows(client, monkeypatch, tmp_path):
    import sistela.services

    pid = project(client)
    good = ParsedLine("1", "Valid", "", "m", Decimal("1"), "", "Material", 1, "[]")
    bad = ParsedLine("2", "Invalid", "", "m", Decimal("-1"), "", "Work", 1, "[]")
    monkeypatch.setattr(
        sistela.services, "parse_pdf", lambda _: PdfResult(1, "text", [good, bad], [1])
    )
    response = client.post(
        f"/projects/{pid}/imports/pdf", files={"file": ("test.pdf", b"%PDF-test")}
    )
    assert response.json()["status"] == "failed"
    assert client.get(f"/projects/{pid}/lines").json() == []
    engine = make_engine(tmp_path)
    with Session(engine) as session:
        assert session.scalars(select(EstimateLine)).all() == []
    engine.dispose()


def test_origin_host_and_missing_project(client):
    assert client.get("/health").json()["external_ai"] is False
    assert client.get("/health", headers={"Origin": "https://attacker.example"}).status_code == 403
    assert client.get("/health", headers={"Host": "attacker.example"}).status_code == 400
    assert client.get("/projects/missing/lines").status_code == 404
    assert client.post("/projects", json={"name": " ", "system_type": "GSS"}).status_code == 422


def test_upload_limits_and_file_type(client, monkeypatch):
    import sistela.api

    monkeypatch.setattr(sistela.api, "MAX_FILE_BYTES", 8)
    pid = project(client)
    endpoint = f"/projects/{pid}/imports/pdf"
    assert client.post(endpoint, files={"file": ("x.xlsx", b"123")}).status_code == 415
    assert client.post(endpoint, files={"file": ("x.pdf", b"")}).status_code == 422
    assert client.post(endpoint, files={"file": ("x.pdf", b"123456789")}).status_code == 413
    assert (
        client.post(endpoint, files={"file": ("x.pdf", b"x" * (1024 * 1024 + 9))}).status_code
        == 413
    )


def test_unverified_exporters_cannot_write(tmp_path):
    from sistela.ports import DbfArchiveExporter, DisabledAiMappingProvider, PackageTextExporter

    for exporter in (DbfArchiveExporter(), PackageTextExporter()):
        with pytest.raises(NotImplementedError):
            exporter.export(None, [], tmp_path / "archive.dbf")
    assert list(tmp_path.iterdir()) == []
    assert DisabledAiMappingProvider().suggest("Confidential", "GSS") == []
