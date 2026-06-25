#!/usr/bin/env python3
"""Validate popular_search_terms.jsonl schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate_object(obj: object, line_num: int, path: Path) -> list[str]:
    errors: list[str] = []
    prefix = f"{path}:{line_num}"

    if not isinstance(obj, dict):
        return [f"{prefix}: expected JSON object"]

    marketplace = obj.get("marketplace")
    if not isinstance(marketplace, str) or not marketplace.strip():
        errors.append(f"{prefix}: 'marketplace' must be a non-empty string")

    languages = obj.get("languages")
    if not isinstance(languages, list) or not languages:
        errors.append(f"{prefix}: 'languages' must be a non-empty array")
        return errors

    for lang_idx, lang_entry in enumerate(languages, start=1):
        lang_prefix = f"{prefix}:languages[{lang_idx}]"
        if not isinstance(lang_entry, dict):
            errors.append(f"{lang_prefix}: expected object")
            continue

        language = lang_entry.get("language")
        if not isinstance(language, str) or not language.strip():
            errors.append(f"{lang_prefix}: 'language' must be a non-empty string")

        search_terms = lang_entry.get("searchTerms")
        if not isinstance(search_terms, list) or not search_terms:
            errors.append(f"{lang_prefix}: 'searchTerms' must be a non-empty array")
            continue

        for term_idx, term in enumerate(search_terms, start=1):
            if not isinstance(term, str) or not term.strip():
                errors.append(
                    f"{lang_prefix}:searchTerms[{term_idx}] must be a non-empty string"
                )

    return errors


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    marketplaces: set[str] = set()

    if not path.exists():
        return [f"{path}: file not found"]

    with path.open(encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]

    if not lines:
        return [f"{path}: file is empty"]

    for line_num, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_num}: invalid JSON: {exc}")
            continue

        errors.extend(validate_object(obj, line_num, path))

        marketplace = obj.get("marketplace") if isinstance(obj, dict) else None
        if isinstance(marketplace, str):
            if marketplace in marketplaces:
                errors.append(f"{path}:{line_num}: duplicate marketplace '{marketplace}'")
            marketplaces.add(marketplace)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="JSONL files to validate")
    args = parser.parse_args()

    all_errors: list[str] = []
    for file_arg in args.files:
        all_errors.extend(validate_file(Path(file_arg)))

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print(f"OK: validated {len(args.files)} file(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
