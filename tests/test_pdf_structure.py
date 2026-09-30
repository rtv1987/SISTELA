import json
from decimal import Decimal
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from pdf_factory import items, make_pdf

from sistela.api import create_app
from sistela.db import migrate
from sistela.parsers.pdf import PdfImportError, parse_pdf


@pytest.mark.parametrize(
    "variant",
    [
        "no_title",
        "unfamiliar_title",
        "reordered",
        "no_borders",
        "wrapped",
        "no_numbers",
        "no_reference",
        "one_work",
        "materials",
        "works",
        "mixed",
        "decimals",
        "punctuation",
        "no_headers",
        "unknown_units",
        "unknown_type",
        "header_words_in_data",
    ],
)
def test_real_pipeline_presentation_variants(tmp_path, variant):
    rows = items()
    kwargs = {}
    if variant == "unfamiliar_title":
        kwargs["title"] = "Component inventory for installation"
    if variant == "reordered":
        kwargs["order"] = [4, 3, 1, 0, 5, 2]
    if variant in {"no_borders", "wrapped"}:
        kwargs["grid"] = False
    if variant == "wrapped":
        rows[1][1] = "Valdymo modulis su\npapildomu kontaktu"
    if variant == "no_numbers":
        kwargs["order"] = [1, 2, 3, 4, 5]
    if variant == "no_reference":
        kwargs["order"] = [0, 1, 3, 4, 5]
    if variant in {"one_work", "mixed"}:
        rows[-1][1] = "Dokumentacijos parengimo ir derinimo darbai"
    if variant == "works":
        rows = items(work=True)
    if variant == "decimals":
        rows[0][4] = "1,125"
    if variant == "punctuation":
        rows[0][3], rows[1][3] = "vnt", "kompl."
    if variant == "no_headers":
        kwargs["headers"] = False
    if variant == "unknown_units":
        for r in rows:
            r[3] = "pak."
    if variant == "unknown_type":
        for r in rows:
            r[1] = f"Neidentifikuotas objektas {r[0]}"
    if variant == "header_words_in_data":
        rows[0][1] = "Modulio aprasymas ir kiekis"
        rows[0][5] = "Pastabos"
    path = make_pdf(tmp_path / "document.pdf", [rows], **kwargs)
    result = parse_pdf(path)
    if result.needs_selection:
        credible = [c for c in result.diagnostics if c["outcome"] == "CREDIBLE"]
        assert credible
        result = parse_pdf(path, max(credible, key=lambda c: c["score"])["id"])
    assert len(result.lines) == 5
    assert [r.quantity for r in result.lines] == [
        Decimal("1.125") if variant == "decimals" and i == 1 else Decimal(i * 3)
        for i in range(1, 6)
    ]
    assert all(json.loads(r.source_raw_text)["bounds"] for r in result.lines)
    if variant == "wrapped":
        assert "papildomu kontaktu" in result.lines[1].project_description
    if variant in {"one_work", "mixed"}:
        assert [r.line_type for r in result.lines].count("Work") == 1
    if variant == "works":
        assert all(r.line_type == "Work" for r in result.lines)
    if variant == "materials":
        assert all(r.line_type == "Material" for r in result.lines)
    if variant == "unknown_type":
        assert all(r.line_type == "Other" for r in result.lines)
        assert all(r.row_type == "UNKNOWN" for r in result.schedule.rows)
    if variant == "decimals":
        assert result.lines[0].quantity == Decimal("1.125")


def test_continuation_repeated_header_and_section_context(tmp_path):
    first = [["", "Darbai", "", "", "", ""]] + items(4)
    second = items(4, start=5)
    result = parse_pdf(make_pdf(tmp_path / "two.pdf", [first, second]))
    assert result.pages == [1, 2]
    assert len(result.lines) == 8
    assert all(r.line_type == "Work" for r in result.lines)


@pytest.mark.parametrize(
    "kind,headings",
    [
        ("index", ["Nr", "Dokumentu sudetis", "Model", "Unit", "Lapu skaicius", ""]),
        ("rooms", ["Room", "Patalpos pavadinimas", "Model", "Unit", "Plotas", ""]),
        ("standards", ["Nr", "Normative standards", "Model", "Unit", "Qty", ""]),
        ("requirements", ["Nr", "Technical requirements", "Model", "Unit", "Qty", ""]),
        ("fire", ["Nr", "Fire resistance", "Model", "Unit", "Qty", ""]),
        ("software", ["Nr", "Software licences", "Model", "Unit", "Qty", ""]),
        ("title", ["Nr", "Signature pareigos", "Model", "Unit", "Qty", ""]),
        ("revisions", ["Nr", "Revision history", "Model", "Unit", "Qty", ""]),
    ],
)
def test_irrelevant_tables_never_automatically_selected(tmp_path, kind, headings):
    rows = [headings] + [
        [str(i), f"Informacinis tekstas {i}", "", "m2", str(i * 10), ""] for i in range(1, 6)
    ]
    path = make_pdf(tmp_path / f"{kind}.pdf", [rows], headers=False)
    try:
        result = parse_pdf(path)
        assert result.needs_selection
    except PdfImportError as exc:
        assert exc.code == "SCHEDULE_NOT_FOUND"
        assert exc.result.diagnostics


def test_irrelevant_tables_before_schedule(tmp_path):
    irrelevant = [["No", "Room area", "", "Unit", "Area", ""]] + [
        [str(i), f"Room {i}", "", "m2", str(i * 5), ""] for i in range(1, 6)
    ]
    result = parse_pdf(
        make_pdf(
            tmp_path / "document.pdf",
            [irrelevant, [["No", "Description", "Model", "Unit", "Qty", "Notes"]] + items()],
            headers=False,
        )
    )
    assert len(result.lines) == 5
    assert result.pages == [2]


def test_ambiguity_persists_and_selection_is_explicit_atomic(tmp_path):
    path = make_pdf(tmp_path / "ambiguous.pdf", [items(), items()])
    migrate(tmp_path)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        pid = client.post("/projects", json={"name": "Choice", "system_type": "GSS"}).json()["id"]
        response = client.post(
            f"/projects/{pid}/imports/pdf", files={"file": ("input.pdf", path.read_bytes())}
        )
        assert response.status_code == 201
        run = response.json()
        assert run["options"]["needs_selection"]
        assert run["warnings"][0]["code"] == "SCHEDULE_NEEDS_SELECTION"
        assert not client.get(f"/projects/{pid}/lines").json()
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        saved = client.get(f"/projects/{pid}/imports").json()[0]
        assert saved["options"] == run["options"]
        candidate = next(c for c in saved["options"]["diagnostics"] if c["outcome"] == "CREDIBLE")
        endpoint = f"/projects/{pid}/imports/{run['id']}/select/{candidate['id']}"
        assert client.post(endpoint + "-invalid").status_code == 422
        other = client.post(
            "/projects", json={"name": "Other project", "system_type": "GSS"}
        ).json()["id"]
        assert client.post(endpoint.replace(pid, other)).status_code == 404
        stored = next((tmp_path / "documents").glob("*.pdf"))
        original = stored.read_bytes()
        stored.write_bytes(b"changed source")
        assert client.post(endpoint).status_code == 409
        assert not client.get(f"/projects/{pid}/lines").json()
        stored.write_bytes(original)
        result = client.post(endpoint)
        assert result.status_code == 200, result.text
        assert not result.json()["options"]["needs_selection"]
        assert len(client.get(f"/projects/{pid}/lines").json()) == 5
        assert client.post(endpoint).status_code == 409
        assert len(client.get(f"/projects/{pid}/lines").json()) == 5


@pytest.mark.fixtures
def test_second_real_pdf_regression(source_file):
    path = source_file("2024.07-616SR-BCB-AG.pdf")
    before = sha256(path.read_bytes()).hexdigest()
    result = parse_pdf(path)
    assert not result.needs_selection
    assert len(result.lines) == 12
    assert sum(r.line_type == "Material" for r in result.lines) == 11
    assert sum(r.line_type == "Work" for r in result.lines) == 1
    assert [r.quantity for r in result.lines] == list(
        map(Decimal, ["1", "2", "10", "1", "9", "68", "4", "1150", "1", "1150", "1", "1"])
    )
    assert [r.unit for r in result.lines] == [
        "kompl.",
        "vnt.",
        "vnt.",
        "vnt.",
        "vnt.",
        "kompl.",
        "vnt.",
        "m",
        "vnt.",
        "m",
        "kompl.",
        "kompl.",
    ]
    assert sha256(path.read_bytes()).hexdigest() == before


def test_index_is_a_hint_not_a_gate(tmp_path):
    path = make_pdf(tmp_path / "indexed.pdf", [items()], title="Schedule navigation 1")
    result = parse_pdf(path)
    chosen = next(c for c in result.diagnostics if c["outcome"] == "SELECTED")
    assert any(r["code"] == "INDEX_HINT" for r in chosen["score_reasons"])
    no_index = parse_pdf(make_pdf(tmp_path / "plain.pdf", [items()]))
    assert len(no_index.lines) == len(result.lines) == 5


def test_loose_compact_lines_are_independent_fallback(tmp_path):
    import pymupdf

    path = tmp_path / "compact.pdf"
    with pymupdf.open() as document:
        page = document.new_page()
        for i in range(1, 7):
            page.insert_text((40, 40 + 20 * i), f"{i} Valdymo modulis vnt. {i * 3}", fontsize=10)
        document.save(path)
    result = parse_pdf(path)
    candidate = next(
        c
        for c in result.diagnostics
        if c["extraction_method"] == "loose" and c["outcome"] in {"SELECTED", "CREDIBLE"}
    )
    if result.needs_selection:
        result = parse_pdf(path, candidate["id"])
    assert len(result.lines) == 6
    assert result.lines[-1].quantity == Decimal("18")


@pytest.mark.parametrize(
    "variant,expected",
    [("confirmed", "Work"), ("conflicting", "Other"), ("unit", "Other"), ("system", "Other")],
)
def test_unknown_classification_uses_only_unambiguous_compatible_confirmed_history(
    tmp_path, variant, expected
):
    from sqlalchemy.orm import Session

    from sistela.db import make_engine
    from sistela.models import HistoricalEstimate, HistoricalImport, HistoricalLine
    from sistela.parsers.common import normalize_text

    rows = items()
    for row in rows:
        row[1] = "Neidentifikuotas objektas"
    path = make_pdf(tmp_path / "unknown.pdf", [rows])
    migrate(tmp_path)
    with Session(make_engine(tmp_path)) as session:
        archive = HistoricalImport(
            source_hash="synthetic",
            source_reference="test",
            source_files=[],
            encoding="cp1257",
            parser_version="test",
        )
        session.add(archive)
        session.flush()
        estimate = HistoricalEstimate(
            historical_import_id=archive.id,
            external_key={},
            name="test",
            project_name="test",
            system_type="GSS",
            system_evidence="test",
            source_reference={},
        )
        session.add(estimate)
        session.flush()
        for kind in ["Work", "Material"] if variant == "conflicting" else ["Work"]:
            session.add(
                HistoricalLine(
                    historical_estimate_id=estimate.id,
                    external_key={},
                    line_type=kind,
                    description=rows[0][1],
                    normalized_description=normalize_text(rows[0][1]),
                    sistela_code="TEST-42",
                    unit="m" if variant == "unit" else "vnt.",
                    section_name="test",
                    system_type="AS" if variant == "system" else "GSS",
                    evidence_type="DIRECT",
                    confidence=Decimal("1"),
                    evidence={},
                    status="CONFIRMED",
                )
            )
        session.commit()
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        pid = client.post(
            "/projects", json={"name": "Classification", "system_type": "GSS"}
        ).json()["id"]
        imported = client.post(
            f"/projects/{pid}/imports/pdf", files={"file": ("unknown.pdf", path.read_bytes())}
        ).json()
        assert imported["rows_detected"] == 5, imported
        lines = client.get(f"/projects/{pid}/lines").json()
        assert all(line["line_type"] == expected for line in lines)
        assert all(line["mapping_status"] != "confirmed" for line in lines)
        if variant == "confirmed":
            assert all(line["sistela_code"] == "TEST-42" for line in lines)
        else:
            assert all(not line["sistela_code"] for line in lines)
        if variant == "confirmed":
            assert (
                json.loads(lines[0]["source_raw_text"])["type_evidence"]["origin"]
                == "confirmed_history"
            )


@pytest.mark.fixtures
@pytest.mark.parametrize(
    "filename,expected", [("2024-10-XX-TDP-GSS.pdf", 21), ("2024.07-616SR-BCB-AG.pdf", 12)]
)
def test_real_document_without_heading_evidence(source_file, monkeypatch, filename, expected):
    import sistela.parsers.pdf_pipeline as pipeline

    discover = pipeline.discover

    def without_heading(path):
        doc = discover(path)
        for page in doc.pages:
            page.text = "Text layer present, heading and index evidence removed"
            page.words = []
        return doc

    monkeypatch.setattr(pipeline, "discover", without_heading)
    result = parse_pdf(source_file(filename))
    assert len(result.lines) == expected
