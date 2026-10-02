"""Local evidence artifact; originals and the source application DB are read-only.

Usage: python scripts/analyze_real_022.py SOURCE_DB PDF OUTPUT_DIRECTORY
The output contains private document/catalog evidence and must not be bundled.
"""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from sistela.auto_mapping import catalog_candidates
from sistela.db import make_engine, migrate
from sistela.dbf_project import project_export_plan
from sistela.export_model import normalized_estimate, save_settings
from sistela.history import historical_suggestions
from sistela.models import EstimateLine, NormativeCatalogSource, NormEntry
from sistela.package_txt import SistelaPackageTxtExporter, validate_txt_export
from sistela.parsers.common import normalize_text
from sistela.schemas import ProjectCreate
from sistela.services import create_project, import_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_db", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "sistela.sqlite3"
    if target.exists():
        raise RuntimeError("Use a fresh analysis directory; existing evidence is preserved")
    with (
        closing(sqlite3.connect(args.source_db.resolve().as_uri() + "?mode=ro", uri=True)) as source,
        closing(sqlite3.connect(target)) as dest,
    ):
        source.backup(dest)
    migrate(args.output)
    with Session(make_engine(args.output)) as session:
        project = create_project(
            session, ProjectCreate(name="GSS 12 rows acceptance 022", system_type="GSS")
        )
        import_pdf(session, args.output, project.id, args.pdf.name, args.pdf.read_bytes())
        save_settings(session, "sistela", {"parameter89": 0})
        save_settings(session, "project:" + project.id, {"filename": "REAL022"})
        model = normalized_estimate(session, project.id)
        mapped = {r["id"]: r for section in model["sections"] for r in section["rows"]}
        source = session.scalar(
            select(NormativeCatalogSource).where(NormativeCatalogSource.active.is_(True))
        )
        catalog = list(
            session.scalars(
                select(NormEntry).where(
                    NormEntry.source_id == source.id,
                    NormEntry.kind.in_(["resource", "material", "resource_price", "rate"]),
                )
            )
        )
        investigation = []
        for line in session.scalars(
            select(EstimateLine)
            .where(EstimateLine.project_id == project.id)
            .order_by(EstimateLine.sort_order)
        ):
            candidates = catalog_candidates(session, line)
            model_key = normalize_text(line.technical_reference)
            exact_models = [
                {
                    "code": e.code,
                    "description": e.description,
                    "unit": e.unit,
                    "file": e.filename,
                    "record": e.record_number,
                }
                for e in catalog
                if model_key and model_key == normalize_text(str(e.payload.get("MARKE", "")))
            ]
            investigation.append(
                {
                    **mapped[line.id],
                    "model_reference": line.technical_reference,
                    "source_position": line.source_position,
                    "exact_model_matches_full_catalog": exact_models,
                    "historical_candidates": historical_suggestions(session, line),
                    "catalog_candidates": [
                        {
                            **c,
                            "record": session.get(NormEntry, c["catalog_id"]).record_number,
                            "file": session.get(NormEntry, c["catalog_id"]).filename,
                            "raw_price_evidence": {
                                k: v
                                for k, v in session.get(NormEntry, c["catalog_id"]).payload.items()
                                if k.startswith("KAI")
                                or k in {"KDAT", "KARINKOS", "KABAZINE", "GALIOJA"}
                            },
                        }
                        for c in candidates[:10]
                    ],
                }
            )
        report = validate_txt_export(model)
        artifacts = {
            "investigation.json": investigation,
            "REAL022.prepared.json": model,
            "REAL022.validation.json": report,
            "DBF022.state.json": project_export_plan(session, project.id),
        }
        for name, data in artifacts.items():
            (args.output / name).write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        if not report["errors"]:
            (args.output / "REAL022.TXT").write_bytes(SistelaPackageTxtExporter().export(model))
        # Explicitly requested zero/unpriced acceptance experiment, never applied
        # to the real project. The omitted-price variant has no documented form.
        experiment = {
            **model,
            "filename": "ZERO022",
            "complex": {"code": "TEST022", "name": "EXPERIMENTAL ACCEPTANCE ONLY"},
            "object": {"code": "1", "name": "Disposable price test"},
            "estimate": {"code": "1", "name": "ZERO PRICE TEST"},
            "common_issues": [],
            "sections": [
                {
                    "id": "test",
                    "code": "1",
                    "name": "Test",
                    "rows": [
                        {
                            "id": "test",
                            "selected_code": "TST022Z",
                            "code_type": "custom",
                            "row_type": "Material",
                            "source_quantity": "1",
                            "target_quantity": "1",
                            "source_unit": "vnt.",
                            "target_unit": "vnt.",
                            "conversion_valid": True,
                            "output_description": "EXPERIMENTAL unpriced material",
                            "price": "0",
                            "options": {"mark": "S", "ngr": 12},
                        }
                    ],
                }
            ],
        }
        (args.output / "ZERO022.TXT").write_bytes(SistelaPackageTxtExporter().export(experiment))
        print(
            "Analysis complete:",
            len(investigation),
            "rows;",
            len(report["errors"]),
            "genuine unresolved fields. Evidence:",
            args.output,
        )


if __name__ == "__main__":
    main()
