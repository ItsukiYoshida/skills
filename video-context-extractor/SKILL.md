---
name: video-context-extractor
description: Extract useful context from local video files or YouTube URLs using ffprobe, ffmpeg, and optional yt-dlp. Use when Codex needs to inspect video content, summarize what happens in a video, sample frames from a movie/screencast/recording/YouTube video, identify scene or UI changes, build visual context before answering questions about a video, or prepare representative frames and metadata for multimodal analysis. Assumes ffmpeg and ffprobe are installed; YouTube URL preparation requires yt-dlp or uvx.
---

# Video Context Extractor

## Overview

Use ffprobe and ffmpeg to convert a video into context Codex can inspect: metadata, representative frames, optional scene-change frames, and optional audio extraction. For YouTube URLs, first use yt-dlp to prepare local artifacts, then run the normal local-video extraction workflow. Treat generated manifests, subtitles, and images as intermediate evidence before summarizing or making claims about the video.

## Workflow

1. Confirm the input is a local video path or YouTube URL and decide the analysis goal: visual summary, UI-state inspection, scene-change detection, or evidence extraction for a specific question.
2. For YouTube URLs, run `scripts/prepare_youtube_context.py` first to download local video/audio, subtitles, info JSON, and `youtube_manifest.json`.
3. Run `scripts/extract_video_context.py` on the prepared local video to generate `manifest.json`, sampled frame JPEGs, and optional audio.
4. Read `youtube_manifest.json` when present, then `manifest.json`, to understand source metadata, duration, dimensions, streams, and extracted artifacts.
5. Inspect representative frames with `view_image`; use `detail: "original"` only when exact UI text, coordinates, or small visual details matter.
6. Increase or narrow sampling only after seeing the first pass. Prefer targeted windows over extracting many redundant frames.
7. Summarize from observed evidence. State uncertainty when audio, small text, or fast motion was not inspected directly.

## Quick Start

Create a compact evidence set:

```bash
python3 /path/to/video-context-extractor/scripts/extract_video_context.py input.mp4 --output-dir /tmp/video-context
```

Prepare a YouTube video, then extract frames from the downloaded local file:

```bash
python3 /path/to/video-context-extractor/scripts/prepare_youtube_context.py "https://www.youtube.com/watch?v=..." --output-dir /tmp/youtube-context
python3 /path/to/video-context-extractor/scripts/extract_video_context.py "<primary_video from /tmp/youtube-context/youtube_manifest.json>" --output-dir /tmp/youtube-context/frames
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

For YouTube audio-only preparation:

```bash
python3 /path/to/video-context-extractor/scripts/prepare_youtube_context.py "https://www.youtube.com/watch?v=..." --output-dir /tmp/youtube-context --audio
```

## YouTube Handling

Use YouTube support as a preparation step, not as a replacement for local video inspection. `prepare_youtube_context.py` writes `youtube_manifest.json` that classifies downloaded video, audio, subtitle, metadata, and other files. Use `primary_video` from that manifest as the input to `extract_video_context.py`.

By default, playlist expansion is disabled to avoid unexpectedly large downloads. Pass `--playlist` only when the user explicitly wants playlist processing. For videos that require an authenticated browser session, pass a cookies file with `--cookies`.

Do not rely on subtitles alone for visual claims. Do not rely on sampled frames alone for exact speech. Respect the user's rights and access to the source video, and avoid downloading more content than needed for the requested analysis.

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
- `scripts/prepare_youtube_context.py`: Prepare local files from a YouTube URL with yt-dlp or uvx, including video/audio, subtitles, info JSON, and `youtube_manifest.json`.
- `references/granularity.md`: Guidance for selecting sampling mode, frame count, and follow-up extraction strategy.
