#!/usr/bin/env python3
"""Run the default goal acceptance review with `claude -p`.

This helper builds a stable review prompt from goal/checkpoint evidence, invokes
Claude Code in print mode, writes the raw review output, then classifies the
terminal review status. The prompt is materialized as a file and passed to
Claude on stdin so large goal context does not appear in the process list.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONTRACT = SKILL_DIR / "references" / "review_gate.md"


def _read_optional(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def _classify(raw: str) -> dict[str, Any]:
    sys.path.insert(0, str(SCRIPT_DIR))
    from validate_review_acceptance import classify  # pylint: disable=import-error

    return classify(raw)


def _build_prompt(args: argparse.Namespace) -> str:
    contract_path = Path(args.contract) if args.contract else DEFAULT_CONTRACT
    sections = [
        "# Role",
        (
            "You are the final acceptance review gate for a checkpointed Codex "
            "goal. Review only; do not implement changes."
        ),
        "# Review Roles",
        "- Implementation reviewer: validate behavior against checkpoints.",
        "- Verification reviewer: validate test and evidence sufficiency.",
        "- Scope reviewer: validate unintended changes, user constraints, and drift.",
        "# Required Output Contract",
        contract_path.read_text(encoding="utf-8"),
        "# Goal Objective",
        _read_optional(args.goal_objective),
        "# Checkpoints",
        _read_optional(args.checkpoints),
        "# Evidence",
        _read_optional(args.evidence),
        "# Changed Files",
        _read_optional(args.changed_files),
        "# Extra Context",
        args.extra_context or "",
        "# Instruction",
        (
            "Return exactly one terminal status: ACCEPTED if no required fixes "
            "remain, otherwise CHANGES_REQUESTED with actionable findings."
        ),
    ]
    return "\n\n".join(section for section in sections if section != "")


def _default_prompt_path(output_path: Path) -> Path:
    return output_path.with_name(output_path.name + ".prompt.md")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a claude -p acceptance review for a checkpointed goal."
    )
    parser.add_argument(
        "--goal-objective",
        help="Goal objective file. Required unless --prompt-file is provided.",
    )
    parser.add_argument("--checkpoints", help="Checkpoint status file.")
    parser.add_argument("--evidence", help="Verification evidence file.")
    parser.add_argument("--changed-files", help="Changed file summary.")
    parser.add_argument("--contract", help="Review contract file.")
    parser.add_argument("--extra-context", help="Additional inline context.")
    parser.add_argument("--output", required=True, help="Path for raw Claude review output.")
    parser.add_argument(
        "--prompt-file",
        help="Existing prompt file to send to Claude instead of building one.",
    )
    parser.add_argument(
        "--prompt-output",
        help="Path to save the generated prompt. Defaults to <output>.prompt.md.",
    )
    parser.add_argument("--stderr-output", help="Optional path to save Claude stderr.")
    parser.add_argument("--cwd", default=".", help="Working directory for claude.")
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=180,
        help="Maximum seconds to wait for claude -p before returning UNKNOWN.",
    )
    parser.add_argument(
        "--max-prompt-chars",
        type=int,
        default=60000,
        help="Fail before invoking Claude if the generated prompt is too large.",
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help="Claude executable name or path.",
    )
    parser.add_argument(
        "--permission-mode",
        default=None,
        help="Optional Claude permission mode, for example dontAsk.",
    )
    args = parser.parse_args()
    if not args.prompt_file and not args.goal_objective:
        parser.error("--goal-objective is required unless --prompt-file is provided")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.prompt_file:
        prompt_output = Path(args.prompt_file)
    else:
        prompt = _build_prompt(args)
        prompt_output = Path(args.prompt_output) if args.prompt_output else _default_prompt_path(output_path)
        prompt_output.parent.mkdir(parents=True, exist_ok=True)
        prompt_output.write_text(prompt, encoding="utf-8")

    prompt_chars = len(prompt_output.read_text(encoding="utf-8"))
    if prompt_chars > args.max_prompt_chars:
        result = {
            "accepted": False,
            "status": "UNKNOWN",
            "error": "prompt_too_large",
            "prompt_chars": prompt_chars,
            "prompt_file": str(prompt_output),
            "max_prompt_chars": args.max_prompt_chars,
        }
        output_path.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 2

    command = [
        args.claude_bin,
        "-p",
        "--output-format",
        "text",
        "--no-session-persistence",
    ]
    if args.permission_mode:
        command.extend(["--permission-mode", args.permission_mode])

    started = time.monotonic()
    try:
        with prompt_output.open("r", encoding="utf-8") as prompt_stdin:
            completed = subprocess.run(
                command,
                cwd=args.cwd,
                stdin=prompt_stdin,
                check=False,
                text=True,
                capture_output=True,
                timeout=args.timeout_sec,
            )
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.monotonic() - started, 3)
        result = {
            "accepted": False,
            "status": "UNKNOWN",
            "error": "claude_timeout",
            "elapsed_sec": elapsed,
            "prompt_file": str(prompt_output),
            "timeout_sec": args.timeout_sec,
        }
        output_path.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
        if args.stderr_output:
            stderr_output = Path(args.stderr_output)
            stderr_output.parent.mkdir(parents=True, exist_ok=True)
            stderr_output.write_text(exc.stderr or "", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 2

    output_path.write_text(completed.stdout, encoding="utf-8")

    if completed.stderr:
        sys.stderr.write(completed.stderr)
        if args.stderr_output:
            stderr_output = Path(args.stderr_output)
            stderr_output.parent.mkdir(parents=True, exist_ok=True)
            stderr_output.write_text(completed.stderr, encoding="utf-8")

    if completed.returncode != 0:
        if not completed.stdout:
            result = {
                "accepted": False,
                "status": "UNKNOWN",
                "error": "claude_failed_without_stdout",
                "returncode": completed.returncode,
            }
            output_path.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
        return completed.returncode

    result = _classify(completed.stdout)
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "UNKNOWN":
        return 2
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
