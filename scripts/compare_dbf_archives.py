"""Read-only semantic comparison; exit 0 SAME, 1 DIFFERENT/invalid."""
import argparse
import json
from pathlib import Path

from sistela.dbf_archive import compare_archives, read_directory
from sistela.parsers.dbf import DbfReadError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    args = parser.parse_args()
    try:
        result = compare_archives(read_directory(args.left), read_directory(args.right))
        valid = not result["left_relationship_errors"] and not result["right_relationship_errors"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "SAME" and valid else 1
    except (DbfReadError, OSError) as exc:
        print(json.dumps({"status": "DIFFERENT", "differences": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
