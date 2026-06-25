#!/usr/bin/env python3
"""Extract and normalize JSONL marketplace lines from a Jira ticket description."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Iterable


CODE_BLOCK_PATTERNS = [
    re.compile(r"\{code(?::\w+)?\}(.*?)\{code\}", re.DOTALL | re.IGNORECASE),
    re.compile(r"```(?:\w+)?\s*(.*?)```", re.DOTALL),
]


def extract_code_block(text: str) -> str:
    for pattern in CODE_BLOCK_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    raise ValueError(
        "No code block found in Jira description. "
        "Expected {code:java}...{code} or fenced ``` block."
    )


def iter_json_lines(block: str) -> Iterable[str]:
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or not line.startswith("{"):
            continue
        yield line


def normalize_line(line: str, line_num: int) -> str:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON on extracted line {line_num}: {exc}") from exc

    if not isinstance(obj, dict):
        raise ValueError(
            f"Line {line_num} must be a JSON object, got {type(obj).__name__}"
        )

    marketplace = obj.get("marketplace")
    if not isinstance(marketplace, str) or not marketplace.strip():
        raise ValueError(f"Line {line_num} missing non-empty 'marketplace' field")

    return json.dumps(obj, ensure_ascii=False)


def parse_description(text: str) -> list[str]:
    block = extract_code_block(text)
    normalized: list[str] = []
    seen: set[str] = set()

    for idx, line in enumerate(iter_json_lines(block), start=1):
        normalized_line = normalize_line(line, idx)
        obj = json.loads(normalized_line)
        marketplace = obj["marketplace"]
        if marketplace in seen:
            raise ValueError(
                f"Duplicate marketplace '{marketplace}' in Jira code block"
            )
        seen.add(marketplace)
        normalized.append(normalized_line)

    if not normalized:
        raise ValueError(
            "Code block found but no JSON marketplace lines were parsed"
        )

    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", "-i",
        help="Path to Jira description text file. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write parsed JSONL to this file instead of stdout.",
    )
    parser.add_argument(
        "--marketplaces", "-m",
        help="Comma-separated marketplace codes to include (e.g. CA,CAN,US). "
             "Omit to include all marketplaces from the ticket.",
    )
    args = parser.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as handle:
            text = handle.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("error: empty input", file=sys.stderr)
        return 1

    try:
        lines = parse_description(text)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.marketplaces:
        allowed = {m.strip().upper() for m in args.marketplaces.split(",")}
        filtered = [
            line for line in lines
            if json.loads(line)["marketplace"].upper() in allowed
        ]
        skipped = len(lines) - len(filtered)
        if skipped:
            print(
                f"filtered: kept {len(filtered)}, skipped {skipped} marketplace(s)",
                file=sys.stderr,
            )
        if not filtered:
            print("error: no marketplaces matched the filter", file=sys.stderr)
            return 1
        lines = filtered

    output_text = "\n".join(lines) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output_text)
    else:
        sys.stdout.write(output_text)

    print(f"parsed {len(lines)} marketplace(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
