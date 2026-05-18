#!/usr/bin/env python3
"""Prepare local artifacts from a YouTube URL for video context extraction."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_FORMAT = "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"
DEFAULT_SUB_LANGS = "ja.*,ja,en.*,en"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("youtube-context"),
        help="Directory to save downloaded artifacts",
    )
    parser.add_argument(
        "-f",
        "--format",
        default=DEFAULT_FORMAT,
        help="yt-dlp format selector for video downloads",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Extract audio as mp3 instead of downloading video",
    )
    parser.add_argument(
        "--sub-langs",
        default=DEFAULT_SUB_LANGS,
        help="Subtitle language selector passed to yt-dlp",
    )
    parser.add_argument(
        "--playlist",
        action="store_true",
        help="Allow playlist downloads. By default only the single URL item is downloaded.",
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        help="Optional cookies file for videos that require an authenticated browser session",
    )
    return parser.parse_args()


def ytdlp_command() -> list[str]:
    ytdlp = shutil.which("yt-dlp")
    if ytdlp:
        return [ytdlp]
    if shutil.which("uvx"):
        return ["uvx", "--from", "yt-dlp", "yt-dlp"]
    raise SystemExit("yt-dlp or uvx is required. Install uv, or put yt-dlp on PATH.")


def snapshot_files(output_dir: Path) -> set[Path]:
    if not output_dir.exists():
        return set()
    return {path for path in output_dir.rglob("*") if path.is_file()}


def classify_files(files: list[Path]) -> dict[str, list[str]]:
    video_exts = {".mp4", ".mkv", ".webm", ".mov"}
    audio_exts = {".mp3", ".m4a", ".opus", ".wav"}
    subtitle_exts = {".srt", ".vtt", ".ass", ".srv1", ".srv2", ".srv3"}
    info_exts = {".json"}

    classified: dict[str, list[str]] = {
        "video": [],
        "audio": [],
        "subtitles": [],
        "metadata": [],
        "other": [],
    }
    for path in files:
        ext = path.suffix.lower()
        if ext in video_exts:
            classified["video"].append(str(path))
        elif ext in audio_exts:
            classified["audio"].append(str(path))
        elif ext in subtitle_exts:
            classified["subtitles"].append(str(path))
        elif ext in info_exts:
            classified["metadata"].append(str(path))
        else:
            classified["other"].append(str(path))
    return classified


def write_manifest(
    output_dir: Path,
    url: str,
    command: list[str],
    returncode: int,
    created_files: list[Path],
    available_files: list[Path],
    elapsed_seconds: float,
) -> Path:
    created = classify_files(created_files)
    available = classify_files(available_files)
    manifest: dict[str, Any] = {
        "source": "youtube",
        "url": url,
        "output_dir": str(output_dir),
        "returncode": returncode,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "command": command,
        "files": available,
        "created_files": created,
        "primary_video": available["video"][0] if available["video"] else None,
        "primary_audio": available["audio"][0] if available["audio"] else None,
    }
    manifest_path = output_dir / "youtube_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    before = snapshot_files(args.output_dir)
    command = ytdlp_command()
    command.extend(
        [
            "--format",
            "bestaudio/best" if args.audio else args.format,
            "--output",
            str(args.output_dir / "%(title).200s [%(id)s].%(ext)s"),
            "--write-info-json",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            args.sub_langs,
        ]
    )
    if not args.playlist:
        command.append("--no-playlist")
    if args.cookies:
        command.extend(["--cookies", str(args.cookies)])
    if args.audio:
        command.extend(["--extract-audio", "--audio-format", "mp3", "--audio-quality", "192K"])
    else:
        command.extend(["--merge-output-format", "mp4"])
    command.append(args.url)

    started = time.monotonic()
    completed = subprocess.run(command, check=False)
    elapsed_seconds = time.monotonic() - started

    after = snapshot_files(args.output_dir)
    created_files = sorted(after - before)
    available_files = sorted(after)
    manifest_path = write_manifest(
        args.output_dir,
        args.url,
        command,
        completed.returncode,
        created_files,
        available_files,
        elapsed_seconds,
    )
    print(str(manifest_path))
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
