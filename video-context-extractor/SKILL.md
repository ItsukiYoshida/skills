---
name: video-context-extractor
description: Extract useful context from local video files using ffprobe and ffmpeg. Use when Codex needs to inspect video content, summarize what happens in a video, sample frames from a movie/screencast/recording, identify scene or UI changes, build visual context before answering questions about a video, or prepare representative frames and metadata for multimodal analysis. Assumes ffmpeg and ffprobe are installed.
---

# Video Context Extractor

## Overview

Use ffprobe and ffmpeg to convert a local video into context Codex can inspect: metadata, representative frames, optional scene-change frames, and optional audio extraction. Treat the generated manifest and images as intermediate evidence before summarizing or making claims about the video.

## Workflow

1. Confirm the input is a local video path and decide the analysis goal: visual summary, UI-state inspection, scene-change detection, or evidence extraction for a specific question.
2. Run `scripts/extract_video_context.py` to generate `manifest.json`, sampled frame JPEGs, and optional audio.
3. Read `manifest.json` first to understand duration, dimensions, streams, and extracted artifacts.
4. Inspect representative frames with `view_image`; use `detail: "original"` only when exact UI text, coordinates, or small visual details matter.
5. Increase or narrow sampling only after seeing the first pass. Prefer targeted windows over extracting many redundant frames.
6. Summarize from observed evidence. State uncertainty when audio, small text, or fast motion was not inspected directly.

## Quick Start

Create a compact evidence set:

```bash
python3 /path/to/video-context-extractor/scripts/extract_video_context.py input.mp4 --output-dir /tmp/video-context
```

For screen recordings or long videos where changes matter:

```bash
python3 /path/to/video-context-extractor/scripts/extract_video_context.py input.mov --output-dir /tmp/video-context --mode both --max-frames 36
```

For a specific time window:

```bash
python3 /path/to/video-context-extractor/scripts/extract_video_context.py input.mp4 --output-dir /tmp/video-context --start 90 --end 150 --mode uniform
```

Extract audio only when dialogue or narration is important and a separate transcription path is available:

```bash
python3 /path/to/video-context-extractor/scripts/extract_video_context.py input.mp4 --output-dir /tmp/video-context --extract-audio
```

## Sampling Strategy

Use the default first pass unless the user asks for frame-accurate analysis. The script chooses evenly spaced timestamps over the selected time range and can optionally add scene-change frames.

- Use `--mode uniform` for tutorials, demos, meetings, or videos where steady progress matters.
- Use `--mode scene` for edited footage, slide decks, cuts, or camera changes.
- Use `--mode both` when the cost of missing a transition is higher than the cost of extra frames.
- Use `--start` and `--end` to narrow analysis after the initial pass.
- Use `--max-frames` to cap context volume; 12-24 frames is usually enough for a first pass, while 36-60 is reasonable for long or dense screen recordings.

See `references/granularity.md` for more detailed granularity guidance.

## Evidence Handling

Do not describe unseen video spans as if they were directly inspected. When only frames were sampled, say the summary is based on sampled frames. If audio was not transcribed, avoid claims about exact speech.

When the user asks a specific question, bias extraction toward the relevant time window, objects, UI state, or visual transition rather than producing a broad generic summary.

## Resources

- `scripts/extract_video_context.py`: Probe a video and extract representative frames, scene-change frames, optional audio, and `manifest.json`.
- `references/granularity.md`: Guidance for selecting sampling mode, frame count, and follow-up extraction strategy.
