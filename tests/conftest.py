import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption(
        "--require-fixtures", action="store_true", help="Fail if private fixtures are missing"
    )


@pytest.fixture
def source_file(request):
    def resolve(name):
        candidates = [ROOT / name, ROOT / "samples/input" / name, ROOT / "samples/sistela" / name]
        if name == "2024-10-XX-TDP-GSS.pdf":
            candidates += [
                ROOT / "2024-10-XX-TDP-GSS(1).pdf",
                ROOT / "samples/input/2024-10-XX-TDP-GSS(1).pdf",
            ]
        for path in candidates:
            if path.is_file():
                return path
        if request.config.getoption("--require-fixtures"):
            pytest.fail(f"Missing required source fixture: {name}")
        pytest.skip(f"Private source fixture not provided: {name}")

    return resolve


@pytest.fixture
def manifest():
    return json.loads((ROOT / "samples/manifest.json").read_text(encoding="utf-8"))
