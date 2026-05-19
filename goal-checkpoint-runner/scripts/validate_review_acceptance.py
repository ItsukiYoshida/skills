#!/usr/bin/env python3
"""Classify goal review output as ACCEPTED or CHANGES_REQUESTED.

The script accepts plain text or JSON from a file path or stdin. It exits 0 only
when the review is clearly accepted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ACCEPTED = "ACCEPTED"
CHANGES_REQUESTED = "CHANGES_REQUESTED"


def _read_input(path: str | None) -> str:
    if path and path != "-":
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _normalize_status(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
    if normalized in {"ACCEPT", "APPROVED", "APPROVE"}:
        return ACCEPTED
    if normalized in {"REQUEST_CHANGES", "CHANGE_REQUESTED", "NEEDS_CHANGES"}:
        return CHANGES_REQUESTED
    if normalized in {ACCEPTED, CHANGES_REQUESTED}:
        return normalized
    return None


def _from_json(raw: str) -> tuple[str | None, int | None]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, None

    if isinstance(parsed, dict):
        status = _normalize_status(parsed.get("status") or parsed.get("result"))
        findings = parsed.get("findings")
        finding_count = len(findings) if isinstance(findings, list) else None
        if status == ACCEPTED and finding_count not in (None, 0):
            return CHANGES_REQUESTED, finding_count
        return status, finding_count

    if isinstance(parsed, str):
        return _normalize_status(parsed), None

    return None, None


def classify(raw: str) -> dict[str, Any]:
    stripped = raw.strip()
    status, finding_count = _from_json(stripped)

    if status is None:
        first_line = stripped.splitlines()[0].strip() if stripped else ""
        status = _normalize_status(first_line)

    if status is None:
        upper = stripped.upper()
        if "CHANGES_REQUESTED" in upper or "REQUEST_CHANGES" in upper:
            status = CHANGES_REQUESTED
        elif upper == ACCEPTED:
            status = ACCEPTED
        else:
            status = "UNKNOWN"

    return {
        "accepted": status == ACCEPTED,
        "status": status,
        "finding_count": finding_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exit 0 only when review output is clearly ACCEPTED."
    )
    parser.add_argument(
        "review_output",
        nargs="?",
        default="-",
        help="Path to review output, or '-' / omitted for stdin.",
    )
    args = parser.parse_args()

    result = classify(_read_input(args.review_output))
    print(json.dumps(result, sort_keys=True))

    if result["status"] == "UNKNOWN":
        return 2
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
