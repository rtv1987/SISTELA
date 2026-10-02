import hashlib
import json
from types import SimpleNamespace

import pytest
from test_package_txt import model

from sistela.install_check import verify_install
from sistela.package_evidence import package_description, price_case
from sistela.package_txt import SistelaPackageTxtExporter, validate_txt_export


@pytest.mark.parametrize(
    "original,expected",
    [
        (
            "Gaisrinės signalizacijos kabelis 1x2x1,0 mm2",
            "Gaisrinės signalizacijos kabelis 1x2x1.0 mm2",
        ),
        (
            "PVC vamzdelis D20, su tvirtinimo elementais",
            "PVC vamzdelis D20; su tvirtinimo elementais",
        ),
        (
            "Darbai pagal sudėties žiniaraštį, dokumentacijos parengimas, paleidimas ir derinimas",
            "Darbai pagal sudėties žiniaraštį; dokumentacijos parengimas; paleidimas ir derinimas",
        ),
    ],
)
def test_real_text_corrections_preserve_source_and_numeric_meaning(original, expected):
    result = package_description(original)
    assert result["original"] == original and result["text"] == expected and result["rules"]
    assert package_description(result["text"])["text"] == expected
    value = model()
    row = value["sections"][0]["rows"][0]
    row["output_description"] = original
    assert "P=" + expected in SistelaPackageTxtExporter().export(value).decode("cp1257")
    assert row["output_description"] == original


def test_no_invented_120_character_description_limit():
    value = model()
    row = value["sections"][0]["rows"][0]
    row["output_description"] = "Pilnas pavadinimas " * 20
    assert package_description(row["output_description"])[
        "text"
    ] in SistelaPackageTxtExporter().export(value).decode("cp1257")


@pytest.mark.parametrize(
    "kind,payload,category,required",
    [
        ("material", {"KAI2610": "1.25"}, "A", False),
        ("resource_price", {"KAI2510": "1.25"}, "B", False),
        ("rate", {}, "B", False),
        ("resource", {"KARINKOS": "1.25"}, "D", None),
        (None, {}, "C", True),
    ],
)
def test_price_categories_do_not_invent_or_promote_old_prices(kind, payload, category, required):
    reference = (
        SimpleNamespace(
            kind=kind, payload=payload, filename="fixture.dbf", record_number=1, code="10"
        )
        if kind
        else None
    )
    result = price_case({"price": None}, reference, "202610")
    assert result["category"] == category and result["explicit_price_required"] is required
    assert result["amount"] is None
    if category == "A":
        assert result["catalog_amount"] == "1.25"
    else:
        assert not result.get("catalog_amount")


def test_unknown_resource_grammar_is_not_reported_as_missing_custom_price():
    value = model()
    row = value["sections"][0]["rows"][0]
    row.update(
        code_type="custom",
        price_case={"category": "D", "reason": "Unproven standalone resource form"},
    )
    assert validate_txt_export(value)["errors"] == [
        {"context": "r", "message": "Unproven standalone resource form"}
    ]


def test_install_manifest_and_all_sqlalchemy_runtime_imports(tmp_path):
    artifact = tmp_path / "component.bin"
    artifact.write_bytes(b"required")
    (tmp_path / "INSTALL-MANIFEST.json").write_text(
        json.dumps({"component.bin": hashlib.sha256(b"required").hexdigest()})
    )
    assert "sqlalchemy.util._collections_cy" in verify_install(tmp_path)
    artifact.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="Damaged"):
        verify_install(tmp_path)
    artifact.unlink()
    with pytest.raises(ValueError, match="Missing"):
        verify_install(tmp_path)
