# Video Extraction Granularity

## First-pass Defaults

Start with a compact extraction. For most videos, 12-24 evenly spaced frames are enough to understand broad structure without flooding context. Use a larger first pass only for dense screen recordings, UI walkthroughs, or fast visual transitions.

## Choosing a Mode

Use `uniform` when the video changes gradually or when time coverage matters: tutorials, product demos, meetings, lectures, long screen recordings, and monitoring footage.

Use `scene` when cuts and visual changes are the important signal: edited videos, slide-heavy videos, camera changes, or short clips with many transitions.

Use `both` when missing a transition would materially affect the answer. This is common for bug reproduction videos, UI walkthroughs, and videos where the user asks "what changed?" or "where did it fail?"

## Frame Counts

- Under 30 seconds: 4-10 frames.
- 30 seconds to 3 minutes: 8-24 frames.
- 3 to 15 minutes: 16-36 frames.
- Over 15 minutes: start with 24-48 frames, then narrow by time window.

Do not keep increasing frame count blindly. After a first pass, identify the relevant time window and run a targeted extraction with `--start` and `--end`.

## Follow-up Extraction

After inspecting the manifest and representative frames:

1. If the answer depends on small UI text, re-run with a larger `--frame-width` or inspect selected frames at original detail.
2. If an event happens between sampled frames, narrow to the surrounding window and increase `--max-frames`.
3. If dialogue or narration matters, use `--extract-audio` and pass the WAV to an available transcription workflow. ffmpeg extraction alone does not provide a transcript.
4. If the video contains rapid motion, prefer a narrow time window over large global sampling.

## Evidence Discipline

Summaries should distinguish between directly inspected frames, metadata from ffprobe, and inferred continuity between frames. Do not claim exact speech, exact UI text, or precise timing unless that evidence was inspected.
