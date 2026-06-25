#!/usr/bin/env python3
"""Merge ticket JSONL lines into popular_search_terms.jsonl by marketplace key."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def format_line(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False)


def load_jsonl(path: Path) -> list[tuple[str, str, dict]]:
    if not path.exists():
        return []

    entries: list[tuple[str, str, dict]] = []
    with path.open(encoding="utf-8") as handle:
        for line_num, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_num}: invalid JSON: {exc}") from exc
            marketplace = obj.get("marketplace")
            if not isinstance(marketplace, str) or not marketplace.strip():
                raise ValueError(f"{path}:{line_num}: missing marketplace")
            entries.append((marketplace, line, obj))
    return entries


def load_updates(path: Path) -> dict[str, dict]:
    updates: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line_num, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_num}: invalid JSON: {exc}") from exc
            marketplace = obj.get("marketplace")
            if not isinstance(marketplace, str) or not marketplace.strip():
                raise ValueError(f"{path}:{line_num}: missing marketplace")
            if marketplace in updates:
                raise ValueError(f"{path}:{line_num}: duplicate marketplace '{marketplace}'")
            updates[marketplace] = obj
    return updates


def merge_entries(
    current: list[tuple[str, str, dict]], updates: dict[str, dict]
) -> tuple[list[str], list[str], list[str], list[str]]:
    replaced: list[str] = []
    unchanged: list[str] = []
    appended: list[str] = []
    merged: list[str] = []
    seen: set[str] = set()

    for marketplace, raw_line, obj in current:
        if marketplace in updates:
            if obj == updates[marketplace]:
                merged.append(raw_line)
                unchanged.append(marketplace)
            else:
                merged.append(format_line(updates[marketplace]))
                replaced.append(marketplace)
            seen.add(marketplace)
        else:
            merged.append(raw_line)
            seen.add(marketplace)

    for marketplace, obj in updates.items():
        if marketplace not in seen:
            merged.append(format_line(obj))
            appended.append(marketplace)

    return merged, replaced, unchanged, appended


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, help="Path to popular_search_terms.jsonl")
    parser.add_argument("--updates", required=True, help="Path to parsed ticket JSONL")
    parser.add_argument("--output", help="Write merged JSONL here (default: stdout)")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print replace/append summary to stderr",
    )
    args = parser.parse_args()

    current_path = Path(args.current)
    updates_path = Path(args.updates)

    try:
        current = load_jsonl(current_path)
        updates = load_updates(updates_path)
        merged, replaced, unchanged, appended = merge_entries(current, updates)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_text = "\n".join(merged) + "\n"
    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    else:
        sys.stdout.write(output_text)

    if args.summary:
        print(f"replaced: {', '.join(replaced) if replaced else '(none)'}", file=sys.stderr)
        if unchanged:
            print(f"unchanged (same content): {', '.join(unchanged)}", file=sys.stderr)
        if appended:
            print(f"appended (new): {', '.join(appended)}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
