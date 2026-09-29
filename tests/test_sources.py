from decimal import Decimal
from hashlib import sha256

import pytest

from sistela.parsers.dbf import DbfReadError, read_dbf


@pytest.mark.fixtures
@pytest.mark.parametrize(
    "name,count,fields",
    [
        ("dd25-04-14.dbf", 391, 50),
        ("nd25-04-14.dbf", 11, 55),
        ("od25-04-14.dbf", 0, 16),
        ("pd25-04-14.dbf", 143, 24),
        ("sd25-04-14.dbf", 104, 45),
        ("td25-04-14.dbf", 48, 42),
    ],
)
def test_real_dbf_read_only(source_file, manifest, name, count, fields):
    path = source_file(name)
    before = path.read_bytes()
    snapshot = read_dbf(path, encoding="cp1257")
    assert snapshot.declared_records == len(snapshot.records) == count
    assert snapshot.deleted_records == 0
    assert len(snapshot.fields) == fields
    assert snapshot.schema() == next(x["fields"] for x in manifest if x["filename"] == name)
    assert snapshot.checksum == next(x["sha256"] for x in manifest if x["filename"] == name)
    assert path.read_bytes() == before
    assert snapshot.declared_encoding == "cp1252"


@pytest.mark.fixtures
def test_encoding_and_decimal(source_file):
    table = read_dbf(source_file("pd25-04-14.dbf"), encoding="cp1257")
    assert table.records[0]["PAVADIN"] == "Įeigos kontrolinis įrenginys"
    assert table.records[0]["KAINA"] == Decimal("350.0000")
    assert isinstance(table.records[0]["KAINA"], Decimal)
    with pytest.raises(DbfReadError):
        read_dbf(source_file("pd25-04-14.dbf"), encoding="ascii")


@pytest.mark.fixtures
def test_all_fixture_hashes(source_file, manifest):
    for entry in manifest:
        path = source_file(entry["filename"])
        assert sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_truncated_dbf_is_not_silently_accepted(tmp_path):
    path = tmp_path / "broken.dbf"
    path.write_bytes(b"broken")
    with pytest.raises(DbfReadError, match="Truncated"):
        read_dbf(path, encoding="cp1257")


@pytest.mark.fixtures
def test_sd_dd_join_and_xlsx_evidence(source_file):
    from openpyxl import load_workbook

    keys = (
        "KOMPLEKSAS",
        "OBJEKTAS",
        "RANGOVAS",
        "SAMATA",
        "SKYRIUS",
        "SUSDARB1",
        "SAM_EILUTE",
        "DET_EILUTE",
    )
    summaries = read_dbf(source_file("sd25-04-14.dbf"), encoding="cp1257").records
    details = read_dbf(source_file("dd25-04-14.dbf"), encoding="cp1257").records
    headers = [row for row in details if row["GRUP"] == 10]
    by_key = {tuple(row[k] for k in keys): row for row in headers}
    assert len(headers) == len(by_key) == len(summaries) == 104
    for summary in summaries:
        header = by_key[tuple(summary[k] for k in keys)]
        assert (summary["IKAINIS"], summary["KIEKIS"]) == (header["IKAINIS"], header["KIEKIS"])
    workbook = load_workbook(source_file("pvz.xlsx"), read_only=True, data_only=False)
    try:
        sheet = workbook["Sheet1"]
        assert sheet["C15"].value == headers[0]["PAVADIN"]
        assert sheet["D38"].value == "100m"
        assert Decimal(str(sheet["E38"].value)) == Decimal("49.14")
    finally:
        workbook.close()
