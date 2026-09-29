"""Read-only package text inspection. Output is private analysis, never a SISTELA package."""
import argparse
import json
from pathlib import Path

from sistela.parsers.package_text import PackageTextParser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--output", type=Path, required=True, help="New JSON file outside source fixtures")
    args = parser.parse_args()
    source, target = args.source.resolve(), args.output.resolve()
    root = Path(__file__).resolve().parents[1]
    if target == source or target.suffix.lower() != ".json" or (root / "samples") in target.parents:
        raise SystemExit("Output must be a new JSON analysis file outside samples and source")
    report = PackageTextParser().parse(source, encoding=args.encoding)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as out:
        json.dump(report.to_dict(), out, ensure_ascii=False, indent=2)
    print(f"lines={len(report.lines)} bytes={report.byte_count} grammar=UNKNOWN sha256={report.sha256}")


if __name__ == "__main__":
    main()
