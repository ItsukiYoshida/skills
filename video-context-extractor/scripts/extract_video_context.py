#!/usr/bin/env python3
"""Extract metadata and representative evidence from a video with ffmpeg/ffprobe."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"Required tool not found on PATH: {name}")
    return path


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def probe(ffprobe: str, input_path: Path) -> dict[str, Any]:
    return run_json(
        [
            ffprobe,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(input_path),
        ]
    )


def parse_duration(probe_data: dict[str, Any]) -> float:
    fmt = probe_data.get("format", {})
    try:
        return float(fmt.get("duration") or 0)
    except (TypeError, ValueError):
        return 0.0


def video_stream(probe_data: dict[str, Any]) -> dict[str, Any] | None:
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    return None


def audio_streams(probe_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [stream for stream in probe_data.get("streams", []) if stream.get("codec_type") == "audio"]


def parse_time(value: str | None, *, default: float) -> float:
    if value is None:
        return default
    parts = value.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except ValueError as exc:
        raise SystemExit(f"Invalid time value: {value}") from exc
    raise SystemExit(f"Invalid time value: {value}")


def auto_frame_count(duration: float, cap: int) -> int:
    if duration <= 0:
        return min(cap, 12)
    if duration <= 30:
        target = math.ceil(duration / 3)
    elif duration <= 180:
        target = math.ceil(duration / 8)
    elif duration <= 900:
        target = math.ceil(duration / 30)
    else:
        target = math.ceil(duration / 90)
    return max(4, min(cap, target))


def uniform_timestamps(start: float, end: float, count: int) -> list[float]:
    if count <= 1 or end <= start:
        return [max(0.0, start)]
    span = end - start
    return [start + span * (index + 0.5) / count for index in range(count)]


def scale_filter(width: int) -> str:
    return f"scale=w=min({width}\\,iw):h=-2"


def extract_uniform_frames(
    ffmpeg: str,
    input_path: Path,
    output_dir: Path,
    timestamps: list[float],
    width: int,
) -> list[dict[str, Any]]:
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict[str, Any]] = []
    for index, timestamp in enumerate(timestamps, start=1):
        out_path = frames_dir / f"uniform_{index:04d}_{timestamp:09.3f}s.jpg"
        run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(input_path),
                "-frames:v",
                "1",
                "-vf",
                scale_filter(width),
                "-q:v",
                "2",
                str(out_path),
            ]
        )
        frames.append({"kind": "uniform", "timestamp": round(timestamp, 3), "path": str(out_path)})
    return frames


def extract_scene_frames(
    ffmpeg: str,
    input_path: Path,
    output_dir: Path,
    start: float,
    end: float,
    max_frames: int,
    threshold: float,
    width: int,
) -> list[dict[str, Any]]:
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = frames_dir / "scene_%04d.jpg"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{max(0.001, end - start):.3f}",
        "-i",
        str(input_path),
        "-vf",
        f"select=gt(scene\\,{threshold}),{scale_filter(width)}",
        "-vsync",
        "vfr",
        "-frames:v",
        str(max_frames),
        "-q:v",
        "2",
        str(pattern),
    ]
    run(command)
    return [
        {"kind": "scene", "timestamp": None, "path": str(path)}
        for path in sorted(frames_dir.glob("scene_*.jpg"))
    ]


def extract_audio(ffmpeg: str, input_path: Path, output_dir: Path, start: float, end: float) -> str:
    out_path = output_dir / "audio.wav"
    run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{max(0.001, end - start):.3f}",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(out_path),
        ]
    )
    return str(out_path)


def build_summary(probe_data: dict[str, Any], duration: float) -> dict[str, Any]:
    vstream = video_stream(probe_data) or {}
    return {
        "duration_seconds": round(duration, 3),
        "format": (probe_data.get("format") or {}).get("format_name"),
        "size_bytes": int((probe_data.get("format") or {}).get("size") or 0),
        "video": {
            "codec": vstream.get("codec_name"),
            "width": vstream.get("width"),
            "height": vstream.get("height"),
            "avg_frame_rate": vstream.get("avg_frame_rate"),
        },
        "audio_stream_count": len(audio_streams(probe_data)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Local video file path")
    parser.add_argument("--output-dir", type=Path, default=Path("video-context"), help="Directory for extracted artifacts")
    parser.add_argument("--mode", choices=["uniform", "scene", "both"], default="uniform", help="Frame extraction mode")
    parser.add_argument("--max-frames", type=int, default=24, help="Maximum frames per selected extraction mode")
    parser.add_argument("--start", help="Start time in seconds, MM:SS, or HH:MM:SS")
    parser.add_argument("--end", help="End time in seconds, MM:SS, or HH:MM:SS")
    parser.add_argument("--scene-threshold", type=float, default=0.35, help="ffmpeg scene-change threshold")
    parser.add_argument("--frame-width", type=int, default=960, help="Maximum extracted frame width")
    parser.add_argument("--extract-audio", action="store_true", help="Extract mono 16 kHz WAV audio for separate transcription")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input does not exist: {args.input}")
    if args.max_frames < 1:
        raise SystemExit("--max-frames must be at least 1")

    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    probe_data = probe(ffprobe, args.input)
    duration = parse_duration(probe_data)
    start = parse_time(args.start, default=0.0)
    end = parse_time(args.end, default=duration or start + 1)
    if end <= start:
        raise SystemExit("--end must be greater than --start")
    if duration > 0:
        start = min(max(0.0, start), duration)
        end = min(max(start + 0.001, end), duration)

    selected_duration = end - start
    frame_count = auto_frame_count(selected_duration, args.max_frames)
    frames: list[dict[str, Any]] = []
    if args.mode in {"uniform", "both"}:
        frames.extend(
            extract_uniform_frames(
                ffmpeg,
                args.input,
                args.output_dir,
                uniform_timestamps(start, end, frame_count),
                args.frame_width,
            )
        )
    if args.mode in {"scene", "both"}:
        frames.extend(
            extract_scene_frames(
                ffmpeg,
                args.input,
                args.output_dir,
                start,
                end,
                args.max_frames,
                args.scene_threshold,
                args.frame_width,
            )
        )

    audio_path = None
    if args.extract_audio:
        audio_path = extract_audio(ffmpeg, args.input, args.output_dir, start, end)

    manifest = {
        "input": str(args.input),
        "output_dir": str(args.output_dir),
        "selection": {
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "mode": args.mode,
            "max_frames": args.max_frames,
            "scene_threshold": args.scene_threshold,
        },
        "summary": build_summary(probe_data, duration),
        "frames": frames,
        "audio": audio_path,
        "probe": probe_data,
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(str(manifest_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
