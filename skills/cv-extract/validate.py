#!/usr/bin/env python3
"""Validate a JSON file against the JSON Resume v1.0.0 schema.

Reports every validation error (not just the first) with JSON Pointer paths.
Extension fields prefixed with `x_` are tolerated even where the schema
disallows additional properties — JSON Resume convention for vendor extensions.

Usage:
    validate.py <path-to-resume.json>

Exit code 0 on success, 1 on validation errors.
"""
from __future__ import annotations

import json
import pathlib
import sys
import copy

try:
    from jsonschema import Draft7Validator, FormatChecker
except ImportError:
    sys.stderr.write("jsonschema is not installed. Install with:  pip install jsonschema\n")
    sys.exit(2)


HERE = pathlib.Path(__file__).parent.resolve()
SCHEMA_PATH = HERE / "jsonresume.schema.json"


def relax_extensions(schema: dict) -> dict:
    """Walk the schema and allow keys starting with `x_` as additional properties.

    JSON Resume's schema sets `additionalProperties: false` on most objects.
    We want vendor extensions (`x_evidence`, `x_industry`, `x_location`, ...) to
    pass — this is the same approach used by JSON-LD and the OpenAPI ecosystem.
    """
    schema = copy.deepcopy(schema)

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and node.get("additionalProperties") is False:
                node["patternProperties"] = {**node.get("patternProperties", {}), "^x_": {}}
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(schema)
    return schema


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: validate.py <resume.json>\n")
        return 2

    target = pathlib.Path(sys.argv[1])
    if not target.exists():
        sys.stderr.write(f"File not found: {target}\n")
        return 2

    schema = json.loads(SCHEMA_PATH.read_text())
    schema = relax_extensions(schema)
    data = json.loads(target.read_text())

    validator = Draft7Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

    if not errors:
        print(f"OK: {target} is valid JSON Resume v1.0.0 (x_* extensions tolerated).")
        return 0

    print(f"FAIL: {len(errors)} validation error(s) in {target}\n")
    for err in errors:
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        print(f"  • /{path}: {err.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
