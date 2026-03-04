"""CLI for PipeSpec -> OPOS compilation."""

from __future__ import annotations

import argparse
import json
import sys

from opos_validator.compiler.api import compile_pipespec_to_opos
from opos_validator.compiler.models import CompileError, CompileOptions
from opos_validator.io import dump_document, load_document


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pipespec2opos")
    p.add_argument("input", help="PipeSpec JSON/YAML file")
    p.add_argument("--out", required=True, help="Output OPOS file path")
    p.add_argument("--format", choices=["json", "yaml"], default=None)
    p.add_argument("--strict", action="store_true", help="Fail on unsupported constructs")
    p.add_argument("--json-report", action="store_true", help="Print compile metadata as JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        pipespec = load_document(args.input)
        opos = compile_pipespec_to_opos(pipespec, options=CompileOptions(strict=args.strict))
        dump_document(opos, args.out, fmt=args.format)

        if args.json_report:
            print(json.dumps({"status": "ok", "output": args.out}, indent=2))
        else:
            print(f"Compiled {args.input} -> {args.out}")
        return 0
    except CompileError as exc:
        print(f"Compile error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
