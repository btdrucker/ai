#!/usr/bin/env python3
"""Fetch CPA debug snapshots and save JSON files to disk."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEBUG_BASE = (
    "https://debug.discover-platform-prod.nikecloud.com/discover/debug/v1"
)


@dataclass
class FlatDims:
    include_channel: bool
    include_marketplace: bool
    include_language: bool
    include_product: bool


@dataclass
class FetchPair:
    marketplace: str
    language: str
    product_code: str
    channel_id: str
    channel_slug: str


@dataclass
class RunStats:
    ok: int = 0
    skipped_exists: int = 0
    error: int = 0
    capped: int = 0


def is_bare_style_code(product_code: str) -> bool:
    return "-" not in product_code


def build_debug_url(
    marketplace: str,
    language: str,
    channel_id: str,
    product_code: str,
) -> str:
    return (
        f"{DEBUG_BASE}/marketplace/{marketplace}/language/{language}"
        f"/consumerChannelId/{channel_id}/productCode/{product_code}/audienceId/cpa"
    )


def fetch_json(url: str, timeout: int = 60) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "dev-fetch-cpa-snapshots/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))




def strip_wrapper_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Remove fields injected by the debug endpoint wrapper (not part of the CPA schema)."""
    record.pop("links", None)
    return record


def normalize_records(payload: Any) -> list[dict[str, Any]]:
    """Unwrap CPA debug responses into a list of product records."""
    if isinstance(payload, dict):
        objects = payload.get("objects")
        if isinstance(objects, list):
            return [strip_wrapper_fields(item) for item in objects if isinstance(item, dict)]
        if payload.get("productCode"):
            return [strip_wrapper_fields(payload)]
        return []

    if isinstance(payload, list):
        return [strip_wrapper_fields(item) for item in payload if isinstance(item, dict)]

    return []


def product_slug_from_record(record: dict[str, Any]) -> tuple[str, str, str]:
    product_code = str(record.get("productCode") or "unknown")
    pdp_url = record.get("pdpUrl") or {}
    url = pdp_url.get("url") if isinstance(pdp_url, dict) else None

    if isinstance(url, str) and url.strip():
        path = urlparse(url).path.strip("/")
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) >= 2:
            slug = segments[-2]
            code = segments[-1]
            return slug, code, f"{slug}--{code}"
        if segments:
            slug = segments[-1]
            return slug, product_code, f"{slug}--{product_code}"

    return product_code, product_code, product_code


def analyze_flat_dims(pairs: list[FetchPair]) -> FlatDims:
    channels = {pair.channel_slug for pair in pairs}
    marketplaces = {pair.marketplace for pair in pairs}
    languages = {pair.language for pair in pairs}
    product_codes = {pair.product_code for pair in pairs}
    products_vary = (
        len(product_codes) > 1
        or any(is_bare_style_code(code) for code in product_codes)
        or len(pairs) > 1
    )

    return FlatDims(
        include_channel=len(channels) > 1,
        include_marketplace=len(marketplaces) > 1,
        include_language=len(languages) > 1,
        include_product=products_vary,
    )


def build_filename(
    record: dict[str, Any],
    pair: FetchPair,
    flat: bool,
    flat_dims: FlatDims,
) -> str:
    _, _, product_part = product_slug_from_record(record)
    parts: list[str] = []

    if flat:
        if flat_dims.include_channel:
            parts.append(pair.channel_slug)
        if flat_dims.include_marketplace:
            parts.append(pair.marketplace)
        if flat_dims.include_language:
            parts.append(pair.language)
        if flat_dims.include_product:
            parts.append(product_part)
        if not parts:
            parts.append(product_part)
        return f"{'--'.join(parts)}.json"

    return f"{product_part}.json"


def build_output_path(
    run_dir: Path,
    pair: FetchPair,
    record: dict[str, Any],
    flat: bool,
    flat_dims: FlatDims,
) -> Path:
    filename = build_filename(record, pair, flat, flat_dims)
    if flat:
        return run_dir / filename
    return (
        run_dir
        / pair.channel_slug
        / pair.marketplace
        / pair.language
        / filename
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_pairs(
    raw_pairs: list[dict[str, Any]],
    default_channel_id: str,
    default_channel_slug: str,
) -> list[FetchPair]:
    pairs: list[FetchPair] = []
    for index, item in enumerate(raw_pairs, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"pairs[{index}] must be an object")

        marketplace = item.get("marketplace")
        language = item.get("language")
        product_code = item.get("productCode")

        if not isinstance(marketplace, str) or not marketplace.strip():
            raise ValueError(f"pairs[{index}].marketplace must be a non-empty string")
        if not isinstance(language, str) or not language.strip():
            raise ValueError(f"pairs[{index}].language must be a non-empty string")
        if not isinstance(product_code, str) or not product_code.strip():
            raise ValueError(f"pairs[{index}].productCode must be a non-empty string")

        channel_id = item.get("channelId", default_channel_id)
        channel_slug = item.get("channelSlug", default_channel_slug)
        if not isinstance(channel_id, str) or not channel_id.strip():
            raise ValueError(f"pairs[{index}].channelId must be a non-empty string")
        if not isinstance(channel_slug, str) or not channel_slug.strip():
            raise ValueError(f"pairs[{index}].channelSlug must be a non-empty string")

        pairs.append(
            FetchPair(
                marketplace=marketplace.strip(),
                language=language.strip(),
                product_code=product_code.strip(),
                channel_id=channel_id.strip(),
                channel_slug=channel_slug.strip(),
            )
        )
    return pairs


def save_records(
    records: list[dict[str, Any]],
    pair: FetchPair,
    run_dir: Path,
    flat: bool,
    flat_dims: FlatDims,
    stats: RunStats,
    max_files: int,
    saved_count: int,
) -> int:
    for record in records:
        if saved_count >= max_files:
            stats.capped += 1
            print("capped: max file limit reached", file=sys.stderr)
            return saved_count

        if not isinstance(record, dict):
            stats.error += 1
            print(
                f"error: non-object record for {pair.product_code} "
                f"({pair.marketplace}/{pair.language})",
                file=sys.stderr,
            )
            continue

        output_path = build_output_path(run_dir, pair, record, flat, flat_dims)
        if output_path.exists():
            stats.skipped_exists += 1
            print(f"skipped-exists: {output_path}")
            continue

        try:
            write_json(output_path, record)
            stats.ok += 1
            saved_count += 1
            print(f"ok: {output_path}")
        except OSError as exc:
            stats.error += 1
            print(f"error: {output_path} ({exc})", file=sys.stderr)

    return saved_count


def process_pair(
    pair: FetchPair,
    run_dir: Path,
    flat: bool,
    flat_dims: FlatDims,
    stats: RunStats,
    max_files: int,
    saved_count: int,
) -> int:
    url = build_debug_url(
        pair.marketplace,
        pair.language,
        pair.channel_id,
        pair.product_code,
    )

    try:
        payload = fetch_json(url)
    except urllib.error.HTTPError as exc:
        stats.error += 1
        print(
            f"error: HTTP {exc.code} for {pair.product_code} "
            f"({pair.marketplace}/{pair.language}) {url}",
            file=sys.stderr,
        )
        return saved_count
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        stats.error += 1
        print(
            f"error: fetch failed for {pair.product_code} "
            f"({pair.marketplace}/{pair.language}): {exc}",
            file=sys.stderr,
        )
        return saved_count

    records = normalize_records(payload)
    if not records:
        if is_bare_style_code(pair.product_code):
            print(
                f"warn: empty colorway array for {pair.product_code} "
                f"({pair.marketplace}/{pair.language})",
                file=sys.stderr,
            )
        else:
            stats.error += 1
            print(
                f"error: no product record for {pair.product_code} "
                f"({pair.marketplace}/{pair.language})",
                file=sys.stderr,
            )
        return saved_count

    return save_records(
        records, pair, run_dir, flat, flat_dims, stats, max_files, saved_count
    )


def load_pairs_arg(pairs_arg: str) -> list[dict[str, Any]]:
    payload = json.loads(pairs_arg)
    if not isinstance(payload, list):
        raise ValueError("--pairs must be a JSON array")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch CPA debug snapshots and write JSON files."
    )
    parser.add_argument("--channel-id", required=True, help="Default consumer channel UUID")
    parser.add_argument("--channel-slug", required=True, help="Default channel slug for paths")
    parser.add_argument(
        "--output-dir",
        default="/tmp/cpa-snapshots",
        help="Base output directory (default: /tmp/cpa-snapshots)",
    )
    parser.add_argument("--max", type=int, default=50, help="Max files to save (default: 50)")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Use flat layout with varying dimensions encoded in filenames",
    )
    parser.add_argument(
        "--pairs",
        required=True,
        help='JSON array of {"marketplace","language","productCode"} objects',
    )
    parser.add_argument(
        "--timestamp",
        help="Override run timestamp folder (YYYY-MM-DD_HHmm). Default: now",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.max < 1:
        print("error: --max must be >= 1", file=sys.stderr)
        return 2

    try:
        raw_pairs = load_pairs_arg(args.pairs)
        pairs = parse_pairs(raw_pairs, args.channel_id, args.channel_slug)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid --pairs: {exc}", file=sys.stderr)
        return 2

    if not pairs:
        print("error: --pairs must contain at least one entry", file=sys.stderr)
        return 2

    timestamp = args.timestamp or datetime.now().strftime("%Y-%m-%d_%H%M")
    run_dir = Path(args.output_dir) / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    flat_dims = analyze_flat_dims(pairs)
    stats = RunStats()
    saved_count = 0

    print(f"run-dir: {run_dir}")
    print(
        "layout: "
        + ("flat" if args.flat else "nested")
        + (
            f" (vary channel={flat_dims.include_channel}, "
            f"marketplace={flat_dims.include_marketplace}, "
            f"language={flat_dims.include_language}, "
            f"product={flat_dims.include_product})"
            if args.flat
            else ""
        )
    )

    for pair in pairs:
        if saved_count >= args.max:
            stats.capped += 1
            break
        saved_count = process_pair(
            pair,
            run_dir,
            args.flat,
            flat_dims,
            stats,
            args.max,
            saved_count,
        )

    print(
        "summary: "
        f"ok={stats.ok} skipped-exists={stats.skipped_exists} "
        f"error={stats.error} capped={stats.capped}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
