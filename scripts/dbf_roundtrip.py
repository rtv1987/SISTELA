"""Developer-only archive experiments. Output is confined to application exports/."""
import argparse
import json
from pathlib import Path

from sistela.dbf_archive import analyze_archive, read_archive
from sistela.dbf_export import DbfExportBlocked, SistelaDbfExporter
from sistela.paths import data_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--destination", required=True, help="New child folder name, not a path")
    parser.add_argument("--record", type=int, help="Physical dd GRUP=10 record, one-based")
    parser.add_argument("--description", help="Change one header description only")
    parser.add_argument("--quantity", help="Deliberately blocked until dependencies are proven")
    args = parser.parse_args()
    if args.quantity is not None:
        parser.error("BLOCKER: quantity/resource/pd/td dependencies and recalculation are UNKNOWN")
    if (args.record is None) != (args.description is None):
        parser.error("--record and --description must be supplied together")
    files = {p.name: p.read_bytes() for p in args.source.glob("*.dbf")}
    mutation = {"record": args.record, "field": "PAVADIN", "value": args.description} if args.record is not None else None
    try:
        result = SistelaDbfExporter(data_dir()).export_clone(files, args.destination, mutation=mutation)
    except DbfExportBlocked as exc:
        parser.error(str(exc))
    (Path(result.destination) / "analysis.json").write_text(
        json.dumps(analyze_archive(read_archive(files)), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result.status, "destination": result.destination,
                      "comparison": result.validation["comparison"], "hashes": result.hashes}, indent=2))


if __name__ == "__main__":
    main()
