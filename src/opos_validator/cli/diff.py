"""CLI for semantic OPOS diff."""

from __future__ import annotations

import argparse
import json
import sys

from opos_validator.diff.api import semantic_diff_opos
from opos_validator.io import load_document


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="opos-diff")
    p.add_argument("left", help="Left OPOS file")
    p.add_argument("right", help="Right OPOS file")
    p.add_argument("--ignore-metadata", action="store_true", help="Ignore metadata changes")
    p.add_argument("--json-report", action="store_true", help="Emit report as JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        left = load_document(args.left)
        right = load_document(args.right)
        report = semantic_diff_opos(left, right)

        if args.json_report:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            if not report.changes:
                print("No semantic changes")
            for change in report.changes:
                print(f"{change.classification:12} {change.change_type:8} {change.path}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
