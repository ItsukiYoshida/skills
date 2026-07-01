#!/usr/bin/env python3
"""Validate the allowed Conventional Commits subset and commit-content policy."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ALLOWED_TYPES = {
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
}

HEADER_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[A-Za-z0-9_.-]+)\))?(?P<bang>!)?: (?P<title>\S.*)$"
)
FOOTER_START_RE = re.compile(
    r"^(?P<token>BREAKING CHANGE|BREAKING-CHANGE|[A-Za-z0-9-]+)(?P<sep>: | #)(?P<value>.+)$"
)
CO_AUTHOR_RE = re.compile(r"^Co-authored-by\s*:", re.IGNORECASE)
COMPOUND_AND_RE = re.compile(r"\band\b", re.IGNORECASE)


def validate_header(header: str) -> list[str]:
    errors: list[str] = []
    match = HEADER_RE.match(header)
    if not match:
        return [
            "header must match '<type>(<scope>)!: <title>' with ': ' before the title"
        ]

    commit_type = match.group("type").lower()
    if commit_type not in ALLOWED_TYPES:
        allowed = ", ".join(sorted(ALLOWED_TYPES))
        errors.append(f"type '{match.group('type')}' is not allowed; use one of: {allowed}")

    scope = match.group("scope")
    if scope is not None and not scope.strip():
        errors.append("scope must be a non-empty noun when present")

    return errors


def title_from_header(header: str) -> str | None:
    match = HEADER_RE.match(header)
    if not match:
        return None
    return match.group("title")


def validate_title_content(header: str) -> list[str]:
    title = title_from_header(header)
    if title is None:
        return []

    if COMPOUND_AND_RE.search(title):
        return [
            "title must describe one debt-unit change; split 'X and Y' into separate commits"
        ]

    return []


def find_footer_start(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if FOOTER_START_RE.match(line):
            return index
    return None


def validate_footers(lines: list[str]) -> list[str]:
    errors: list[str] = []
    footer_start = find_footer_start(lines)
    if footer_start is None:
        return errors

    for offset, line in enumerate(lines[footer_start:], start=footer_start + 1):
        if not line:
            errors.append(f"footer line {offset} must not be blank inside the footer block")
            continue

        match = FOOTER_START_RE.match(line)
        if match:
            token = match.group("token")
            if token.lower() in {"breaking change", "breaking-change"} and token not in {
                "BREAKING CHANGE",
                "BREAKING-CHANGE",
            }:
                errors.append(
                    f"footer line {offset} must use uppercase BREAKING CHANGE or BREAKING-CHANGE"
                )

    return errors


def has_breaking_footer(lines: list[str]) -> bool:
    return any(
        line.startswith("BREAKING CHANGE: ") or line.startswith("BREAKING-CHANGE: ")
        for line in lines
    )


def has_co_author(lines: list[str]) -> bool:
    return any(CO_AUTHOR_RE.match(line) for line in lines)


def has_body_or_footer(lines: list[str]) -> bool:
    return any(line.strip() for line in lines[1:])


def validate_message(message: str, *, title_only: bool, squash: bool) -> list[str]:
    errors: list[str] = []
    if message.endswith("\n"):
        message = message[:-1]

    if not message:
        return ["message must not be empty"]

    lines = message.splitlines()
    if title_only and len(lines) != 1:
        errors.append("PR title validation expects exactly one line")

    header = lines[0]
    errors.extend(validate_header(header))
    errors.extend(validate_title_content(header))

    if len(lines) > 1 and lines[1] != "":
        errors.append("commit body or footers must start after one blank line")

    if not title_only and not squash and has_body_or_footer(lines):
        errors.append(
            "individual commit messages must be title-only; put details in the PR or squash-commit body"
        )

    if not squash and has_co_author(lines):
        errors.append(
            "individual commit messages must not include Co-authored-by trailers"
        )

    if not title_only:
        errors.extend(validate_footers(lines[2:] if len(lines) > 2 else []))

    header_has_bang = bool(HEADER_RE.match(header) and HEADER_RE.match(header).group("bang"))
    footer_is_breaking = has_breaking_footer(lines)
    if title_only and "BREAKING CHANGE" in message:
        errors.append("PR titles cannot carry BREAKING CHANGE footers; use ! in the header")

    if footer_is_breaking and title_only:
        errors.append("PR titles must express breaking changes with ! in the header")

    if header_has_bang and not header.split(": ", 1)[1].strip():
        errors.append("breaking-change title must describe the change")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate commit messages and PR titles against the allowed Conventional Commits subset."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("message", nargs="?", help="message or PR title to validate")
    source.add_argument("--file", type=Path, help="commit message file to validate")
    parser.add_argument(
        "--title-only",
        action="store_true",
        help="validate a single-line PR title or squash-merge title",
    )
    parser.add_argument(
        "--squash",
        action="store_true",
        help="validate a squash-commit message where a body or footers are acceptable",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    message = args.file.read_text() if args.file else args.message
    errors = validate_message(message, title_only=args.title_only, squash=args.squash)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
