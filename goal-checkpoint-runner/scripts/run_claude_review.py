#!/usr/bin/env python3
"""Run the default goal acceptance review with `claude -p`.

This helper builds a stable review prompt, materializes it as a file, invokes
Claude Code in non-interactive print mode, writes the raw Claude output, then
classifies the terminal review status. Reviewer failures are normalized to
UNKNOWN/exit 2 so they cannot be mistaken for CHANGES_REQUESTED findings.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from validate_review_acceptance import classify as classify_review


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_CONTRACT = SKILL_DIR / "references" / "review_gate.md"
DEFAULT_ALLOWED_TOOLS = [
    "Read",
    "Grep",
    "Glob",
    "Bash(git diff:*)",
    "Bash(git log:*)",
    "Bash(git status:*)",
]
DEFAULT_DISALLOWED_TOOLS = ["Edit", "Write", "MultiEdit", "NotebookEdit"]
REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": ["ACCEPTED", "CHANGES_REQUESTED"]},
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "checkpoint": {"type": "string"},
                    "severity": {"type": "string"},
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "problem": {"type": "string"},
                    "required_fix": {"type": "string"},
                },
                "required": ["problem"],
            },
        },
    },
    "required": ["status", "findings"],
}
MAX_INLINE_SETTINGS_CHARS = 65536
MAX_SETTINGS_PATH_CHARS = 4096


def _read_optional(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def _classify(raw: str) -> dict[str, Any]:
    return classify_review(raw)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _unknown(
    output_path: Path,
    error: str,
    **extra: Any,
) -> dict[str, Any]:
    result = {"accepted": False, "status": "UNKNOWN", "error": error}
    result.update(extra)
    _write_json(output_path, result)
    print(json.dumps(result, sort_keys=True))
    return result


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
            "Return a JSON object matching the required schema. Use status "
            "ACCEPTED only when no required fixes remain. Use status "
            "CHANGES_REQUESTED with actionable findings when fixes are required."
        ),
    ]
    return "\n\n".join(section for section in sections if section != "")


def _default_prompt_path(output_path: Path) -> Path:
    return output_path.with_name(output_path.name + ".prompt.md")


def _append_repeated(command: list[str], flag: str, values: list[str]) -> None:
    if values:
        command.append(flag)
        command.extend(values)


def _contains_api_key_helper(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "apiKeyHelper" and bool(item):
                return True
            if _contains_api_key_helper(item):
                return True
    if isinstance(value, list):
        return any(_contains_api_key_helper(item) for item in value)
    return False


def _settings_has_api_key_helper(settings: str | None) -> bool:
    if not settings:
        return False

    stripped = settings.lstrip()
    if stripped.startswith(("{", "[")):
        if len(settings) > MAX_INLINE_SETTINGS_CHARS:
            return False
        raw = settings
    else:
        if len(settings) > MAX_SETTINGS_PATH_CHARS:
            return False
        settings_path = Path(settings).expanduser()
        try:
            if not settings_path.is_file():
                return False
            raw = settings_path.read_text(encoding="utf-8")
        except OSError:
            return False

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return False
    return _contains_api_key_helper(parsed)


def _has_hermetic_auth(args: argparse.Namespace) -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY")) or _settings_has_api_key_helper(
        args.settings
    )


def _build_command(args: argparse.Namespace, cwd: Path) -> list[str]:
    command = [args.claude_bin, "-p"]
    if args.hermetic:
        command.append("--bare")
    else:
        command.append("--strict-mcp-config")

    command.extend([
        "--model",
        args.model,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(REVIEW_SCHEMA, separators=(",", ":")),
        "--permission-mode",
        args.permission_mode,
        "--no-session-persistence",
        "--exclude-dynamic-system-prompt-sections",
        "--add-dir",
        str(cwd),
    ])
    if args.settings:
        command.extend(["--settings", args.settings])
    if args.fallback_model:
        command.extend(["--fallback-model", args.fallback_model])
    if args.max_budget_usd:
        command.extend(["--max-budget-usd", str(args.max_budget_usd)])
    _append_repeated(command, "--allowedTools", args.allowed_tool)
    _append_repeated(command, "--disallowedTools", args.disallowed_tool)
    return command


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
        default=300,
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
        "--model",
        default="opus",
        help="Claude model alias or full model name for review.",
    )
    parser.add_argument(
        "--fallback-model",
        default="sonnet",
        help="Fallback model for claude -p overloads. Empty string disables it.",
    )
    parser.add_argument(
        "--max-budget-usd",
        default="2",
        help="Maximum Claude API spend for one review. Empty string disables it.",
    )
    parser.add_argument(
        "--permission-mode",
        default="default",
        help="Claude permission mode for review. Default: default.",
    )
    parser.add_argument(
        "--hermetic",
        action="store_true",
        help="Use claude --bare. This disables OAuth/keychain auth and requires ANTHROPIC_API_KEY or apiKeyHelper.",
    )
    parser.add_argument(
        "--settings",
        help=(
            "Claude settings JSON or settings file path. Used mainly for "
            "--hermetic apiKeyHelper auth."
        ),
    )
    parser.add_argument(
        "--allowed-tool",
        action="append",
        default=None,
        help="Allowed Claude tool. Repeat to replace the default read-only tool set.",
    )
    parser.add_argument(
        "--disallowed-tool",
        action="append",
        default=None,
        help="Disallowed Claude tool. Repeat to replace the default write-deny set.",
    )
    args = parser.parse_args()
    if not args.prompt_file and not args.goal_objective:
        parser.error("--goal-objective is required unless --prompt-file is provided")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cwd = Path(args.cwd).resolve()
    args.allowed_tool = args.allowed_tool or list(DEFAULT_ALLOWED_TOOLS)
    args.disallowed_tool = args.disallowed_tool or list(DEFAULT_DISALLOWED_TOOLS)

    if args.prompt_file:
        prompt_output = Path(args.prompt_file)
    else:
        prompt = _build_prompt(args)
        prompt_output = Path(args.prompt_output) if args.prompt_output else _default_prompt_path(output_path)
        prompt_output.parent.mkdir(parents=True, exist_ok=True)
        prompt_output.write_text(prompt, encoding="utf-8")

    prompt_chars = len(prompt_output.read_text(encoding="utf-8"))
    if prompt_chars > args.max_prompt_chars:
        _unknown(
            output_path,
            "prompt_too_large",
            prompt_chars=prompt_chars,
            prompt_file=str(prompt_output),
            max_prompt_chars=args.max_prompt_chars,
        )
        return 2

    if args.hermetic and not _has_hermetic_auth(args):
        _unknown(
            output_path,
            "claude_auth_missing_for_hermetic",
            prompt_file=str(prompt_output),
            reason=(
                "--hermetic uses claude --bare, which ignores OAuth/keychain auth. "
                "Set ANTHROPIC_API_KEY or pass --settings with apiKeyHelper."
            ),
        )
        return 2

    command = _build_command(args, cwd)

    started = time.monotonic()
    try:
        with prompt_output.open("r", encoding="utf-8") as prompt_stdin:
            completed = subprocess.run(
                command,
                cwd=cwd,
                stdin=prompt_stdin,
                check=False,
                text=True,
                capture_output=True,
                timeout=args.timeout_sec,
            )
    except FileNotFoundError:
        _unknown(output_path, "claude_not_found", claude_bin=args.claude_bin)
        return 2
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.monotonic() - started, 3)
        if args.stderr_output:
            stderr_output = Path(args.stderr_output)
            stderr_output.parent.mkdir(parents=True, exist_ok=True)
            stderr_output.write_text(exc.stderr or "", encoding="utf-8")
        _unknown(
            output_path,
            "claude_timeout",
            elapsed_sec=elapsed,
            prompt_file=str(prompt_output),
            timeout_sec=args.timeout_sec,
        )
        return 2

    if completed.stderr:
        sys.stderr.write(completed.stderr)
        if args.stderr_output:
            stderr_output = Path(args.stderr_output)
            stderr_output.parent.mkdir(parents=True, exist_ok=True)
            stderr_output.write_text(completed.stderr, encoding="utf-8")

    if completed.returncode != 0:
        if completed.stdout:
            output_path.write_text(completed.stdout, encoding="utf-8")
        _unknown(
            output_path,
            "claude_failed",
            returncode=completed.returncode,
            prompt_file=str(prompt_output),
        )
        return 2

    output_path.write_text(completed.stdout, encoding="utf-8")
    result = _classify(completed.stdout)
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "UNKNOWN":
        return 2
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
