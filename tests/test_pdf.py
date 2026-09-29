import json
from decimal import Decimal
from hashlib import sha256

import pytest

from sistela.parsers.common import normalize_text, normalize_unit, parse_decimal
from sistela.parsers.pdf import PdfImportError, parse_pdf, parse_table


@pytest.mark.fixtures
def test_real_gss_regression(source_file, manifest):
    path = source_file("2024-10-XX-TDP-GSS.pdf")
    before = sha256(path.read_bytes()).hexdigest()
    result = parse_pdf(path)
    assert result.page_count == 17
    assert result.pages == [14]
    assert len(result.lines) == 21
    assert sum(x.line_type == "Material" for x in result.lines) == 11
    assert sum(x.line_type == "Work" for x in result.lines) == 10
    expected = [
        ("Material", "zonu ispletimo modulis", "2", "vnt."),
        ("Material", "akumuliatorius", "2", "vnt."),
        ("Material", "lauko sirena", "1", "vnt."),
        ("Material", "vidaus sirena", "5", "vnt."),
        ("Material", "ranka valdomas", "9", "vnt."),
        ("Material", "dumu detektorius", "28", "kompl."),
        ("Material", "tarpine komutavimo rele", "2", "vnt."),
        ("Material", "kabelis 1x2x0 8", "600", "m"),
        ("Material", "kabelis 3x1 5", "50", "m"),
        ("Material", "pvc vamzdelis", "600", "m"),
        ("Material", "papildomu medziagu", "1", "kompl."),
        ("Work", "ispletimo modulio montavimas", "2", "vnt."),
        ("Work", "rezervinio maitinimo", "2", "vnt."),
        ("Work", "detektoriu montavimas", "28", "vnt."),
        ("Work", "ranka valdomu", "9", "vnt."),
        ("Work", "lauko sirenos", "1", "vnt."),
        ("Work", "vidaus sirenos", "5", "vnt."),
        ("Work", "kabelio montavimas", "650", "m"),
        ("Work", "relinio isejimo", "2", "vnt."),
        ("Work", "instaliacinio vamzdzio", "600", "m"),
        ("Work", "programavimo derinimo", "1", "kompl."),
    ]
    for kind, fragment, quantity, unit in expected:
        matches = [
            line
            for line in result.lines
            if line.line_type == kind and fragment in normalize_text(line.project_description)
        ]
        assert len(matches) == 1, fragment
        assert matches[0].quantity == Decimal(quantity)
        assert matches[0].unit == unit
        assert matches[0].source_page == 14
        assert json.loads(matches[0].source_raw_text)
    assert result.lines[0].technical_reference == "8Z"
    assert result.lines[5].technical_reference == "FD8030"
    assert result.lines[12].technical_reference == "TS2.2"
    assert "dokumentacijos paruošimo darbai" in result.lines[-1].project_description
    assert "MONTAVIMO DARBAI" in result.extracted_text
    assert any(w["code"] == "TYPE_INFERRED" for w in result.warnings)
    assert not any(w["code"] == "ROW_REJECTED" for w in result.warnings)
    assert sha256(path.read_bytes()).hexdigest() == before


def test_reordered_columns_and_decimal_not_fixture_specific():
    rows = [
        ["Kiekis", "Pastabos", "Pavadinimas", "Eil. Nr.", "Mato vnt.", "Modelis"],
        ["", "", "MEDŽIAGOS", "", "", ""],
        ["1 234,125", "Pastaba", "Naujas\nprietaisas", "7.", "v n t .", "ANY-8"],
        ["0", "", "Kabelis", "8.", "100m", ""],
        ["?", "", "Neįskaitomas kiekis", "9.", "m", ""],
    ]
    lines, warnings = parse_table(rows, 3)
    assert len(lines) == 2
    assert lines[0].project_description == "Naujas prietaisas"
    assert lines[0].quantity == Decimal("1234.125")
    assert lines[0].source_position == "7"
    assert lines[0].technical_reference == "ANY-8"
    assert lines[1].quantity == Decimal("0")
    assert lines[1].unit == "100m"
    assert [w["code"] for w in warnings] == ["ROW_REJECTED"]


def test_title_and_toc_are_not_rows():
    lines, _ = parse_table([["Sąnaudų kiekių žiniaraštis", "14"], ["Lapas", "Lapų"]], 2)
    assert lines == []


@pytest.mark.parametrize("value", ["NaN", "1x2x0,8", "1,000.25", "1 2", "", "Infinity"])
def test_ambiguous_numbers_rejected(value):
    with pytest.raises(ValueError):
        parse_decimal(value)


def test_units_do_not_erase_scale():
    assert normalize_unit("100 m") == "100m"
    assert normalize_unit("m²") == "m2"
    assert normalize_unit("k o m p l .") == "kompl."


def test_invalid_pdf_has_safe_error(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"SECRET-NOT-A-PDF")
    with pytest.raises(PdfImportError) as caught:
        parse_pdf(path)
    assert caught.value.code == "INVALID_PDF"
    assert "SECRET" not in str(caught.value)


class FakePage:
    def __init__(self, text, tables=()):
        self.text = text
        self.tables = tables

    def dedupe_chars(self):
        return self

    def extract_text(self):
        return self.text

    def extract_tables(self, table_settings):
        return self.tables


class FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


@pytest.mark.parametrize(
    "pages,code",
    [
        ([FakePage("")], "OCR_REQUIRED"),
        ([FakePage("Techninės specifikacijos")], "SCHEDULE_NOT_FOUND"),
        ([FakePage("")] * 301, "PAGE_LIMIT"),
    ],
)
def test_unsupported_pdf_reports_reason(monkeypatch, pages, code):
    import sistela.parsers.pdf

    monkeypatch.setattr(sistela.parsers.pdf.pdfplumber, "open", lambda _: FakePdf(pages))
    with pytest.raises(PdfImportError) as caught:
        parse_pdf(None)
    assert caught.value.code == code


def test_continuation_page_retains_explicit_work_category(monkeypatch):
    import sistela.parsers.pdf

    header = ["Eil.Nr.", "Pavadinimas", "Mato vnt.", "Kiekis"]
    pages = [
        FakePage(
            "Sąnaudų kiekių žiniaraštis",
            [[header, ["Montavimo darbai", None, None, None], ["1", "Prijungimas", "vnt.", "3"]]],
        ),
        FakePage("Lentelės tęsinys", [[header, ["2", "Patikra", "kompl.", "1"]]]),
        FakePage("Brėžinys"),
    ]
    monkeypatch.setattr(sistela.parsers.pdf.pdfplumber, "open", lambda _: FakePdf(pages))
    result = parse_pdf(None)
    assert result.pages == [1, 2]
    assert [line.line_type for line in result.lines] == ["Work", "Work"]


def test_missing_quantity_and_unit_are_visible():
    rows = [["Eil.Nr.", "Pavadinimas", "Mato vnt.", "Kiekis"], ["1", "Neįskaitoma eilutė", "", ""]]
    lines, warnings = parse_table(rows, 2)
    assert not lines
    assert warnings[0]["code"] == "ROW_REJECTED"
