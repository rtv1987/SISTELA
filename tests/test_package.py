import hashlib
import subprocess
import sys

import pytest

from sistela.integration import capabilities
from sistela.parsers.package_text import PackageTextParser


def test_developer_cli_keeps_source_private_and_refuses_overwrite(tmp_path):
    from sistela.db import ROOT

    source = tmp_path / 'input.txt'
    source.write_text('PRIVATE-SOURCE\tN50-1\t2,5', encoding='utf-8')
    target = tmp_path / 'analysis.json'
    args = [sys.executable, str(ROOT / 'scripts/analyze_package.py'), str(source), '--output', str(target)]
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    assert 'grammar=UNKNOWN' in result.stdout and 'PRIVATE-SOURCE' not in result.stdout
    assert 'PRIVATE-SOURCE' in target.read_text(encoding='utf-8')
    before = target.read_bytes()
    assert subprocess.run(args, capture_output=True).returncode != 0
    assert target.read_bytes() == before
    assert source.read_text(encoding='utf-8') == 'PRIVATE-SOURCE\tN50-1\t2,5'


def test_unknown_package_is_losslessly_inspected_not_interpreted(tmp_path):
    data = "Nežinoma\tN50-270\t2,5\r\n\r\n# custom\nPabaiga".encode("utf-8")
    source = tmp_path / "sample.txt"
    source.write_bytes(data)
    report = PackageTextParser().parse(source)
    assert source.read_bytes() == data
    assert report.sha256 == hashlib.sha256(data).hexdigest()
    assert "".join(line.raw + line.ending for line in report.lines) == report.text
    assert report.lines[0].tab_cells[-1] == "2,5"
    assert report.lines[0].code_candidates == ["N50-270"]
    assert report.lines[1].kind == "blank"
    assert report.grammar_status == "UNKNOWN"


def test_encoding_is_explicit_and_strict():
    data = "Įrenginys\t2".encode("cp1257")
    with pytest.raises(ValueError, match="decode"):
        PackageTextParser().parse_bytes(data)
    assert PackageTextParser().parse_bytes(data, encoding="cp1257").text.startswith("Įrenginys")


@pytest.mark.parametrize("data", [b"a\0b", b"x" * (5 * 1024 * 1024 + 1)], ids=["nul", "oversize"])
def test_invalid_package_rejected(data):
    with pytest.raises(ValueError):
        PackageTextParser().parse_bytes(data)


def test_unverified_capabilities_are_not_production():
    by_id = {c["id"]: c for c in capabilities()}
    for name in ("dbf_write", "package_text_export"):
        assert by_id[name]["status"] == ("analysis_only" if name == "dbf_write" else "blocked")
        assert not by_id[name]["production"]
    assert not any(c["writes_to_sistela"] for c in by_id.values())
