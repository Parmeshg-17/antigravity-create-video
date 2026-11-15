---
name: create-video
description: Use when the user requests to create, generate, produce, or render an MP4 video, short video, YouTube Short, Instagram Reel, explainer video, or slide presentation video from a text prompt, script, or topic with voiceover and captions. Do not use for audio-only tasks, static image generation without video output, or when only editing an existing non-generated video file.
---

# Create Video Skill

This skill allows the agent to produce complete, production-ready 1080p MP4 videos from any user prompt, script, or topic. It automatically synthesizes natural AI voiceovers via Microsoft Edge-TTS, formats high-contrast typographic or image slides, applies smooth Ken Burns pan/zoom motion, burns in subtitles, and compiles an MP4 file with synchronized audio.

---

## Workflow Overview

Follow this 5-step procedure whenever a video generation task is requested:

```
[User Request / Topic]
        │
        ▼
1. Verify Environment & Dependencies (Python, FFmpeg, edge-tts, Pillow)
        │
        ▼
2. Generate Structured Storyboard (`output/storyboard.json`)
        │
        ▼
3. Execute Video Generator Script (`generate_video.py`)
        │
        ▼
4. Verify Rendered Output & Streams (`output/final_video.mp4`)
        │
        ▼
5. Present Video Result to the User
```

---

## Step 1: Check and Install Dependencies

Ensure Python 3 and the required libraries are installed.

1. **Verify Python and FFmpeg**:
   ```powershell
   python --version
   ffmpeg -version
   ```
   *Note: If `ffmpeg` is not on the system PATH, the generator script will automatically look for `imageio_ffmpeg` or WinGet/Local paths.*

2. **Verify Python Packages**:
   Install any missing packages using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
   Or install them directly:
   ```bash
   pip install edge-tts pillow imageio-ffmpeg
   ```

---

## Step 2: Determine Aspect Ratio & Format

Analyze the user's prompt to determine the target aspect ratio:

* **Vertical 9:16 (`1080x1920`)**:
  * Triggered by words like: *Short, Reel, TikTok, Vertical, Mobile, Story*.
  * Best for: Quick facts, motivational quotes, viral stories, short explainers.
* **Landscape 16:9 (`1920x1080`)**:
  * Triggered by words like: *YouTube video, Presentation, Landscape, Widescreen, Explainer*.
  * Best for: Educational tutorials, business overviews, deep dives.

*Default to `16:9` unless the user specifies shorts, reels, or vertical format.*

---

## Step 3: Generate the Storyboard (`output/storyboard.json`)

Write a structured JSON file at `output/storyboard.json` containing the narrative arc, scene titles, voiceover text, and styling.

### Storyboard Guidelines:
* **Pacing**: Aim for 3 to 7 scenes total. Each scene should take 4 to 9 seconds of natural speaking time.
* **Narration**: Write concise, punchy, conversational sentences.
* **Titles & Subtitles**: Keep on-screen titles under 6 words so they remain large, legible, and visually impactful.
* **Backgrounds**: Provide distinct complementary gradient colors for each scene (e.g. Navy to Indigo, Slate to Teal, Wine to Crimson) or supply an `image_path` to an existing generated illustration.
* **Motions**: Vary the camera motion across scenes (`zoom_in`, `zoom_out`, `pan_up`, `pan_down`, `shake`).

Refer to [.agents/skills/create-video/references/storyboard_schema.md](file:///C:/Users/parmesh/Desktop/.agents/skills/create-video/references/storyboard_schema.md) for the complete JSON schema.

### Example Generation Command:
Write the storyboard using the `write_file` tool to `output/storyboard.json`.

---

## Step 4: Run the Video Generator Script

Run the built-in generator script located at `.agents/skills/create-video/scripts/generate_video.py`:

```bash
python .agents/skills/create-video/scripts/generate_video.py --storyboard output/storyboard.json --aspect 9:16 --output output/final_video.mp4
```

### Supported CLI Flags:
* `--storyboard <path>`: Path to input storyboard JSON (default: `output/storyboard.json`).
* `--aspect <16:9|9:16>`: Force aspect ratio (overrides storyboard setting).
* `--output <path>`: Output destination for the compiled MP4 (default: `output/final_video.mp4`).
* `--fps <int>`: Video frame rate (default: `30`).
* `--keep-temp`: Retain temporary per-scene audio files for inspection.

The script will:
1. Synthesize natural human-like voiceover audio using Edge-TTS for each scene.
2. Accurately measure the exact audio duration down to milliseconds.
3. Automatically adjust scene video duration to match speech pacing.
4. Render high-resolution frames with modern typography cards or images.
5. Apply smooth Ken Burns camera pan and zoom motions.
6. Burn in high-contrast centered captions at the lower third.
7. Apply seamless crossfade transitions between scenes.
8. Stream and encode high-compatibility H.264/AAC MP4 video with FFmpeg.

---

## Step 5: Verify the Rendered Video

After the generator script finishes, verify that the output video was created and contains valid media streams:

```powershell
python -c "
import os, subprocess
video_path = r'output/final_video.mp4'
if os.path.exists(video_path) and os.path.getsize(video_path) > 100000:
    print(f'Verification passed: {video_path} ({os.path.getsize(video_path) / 1024 / 1024:.2f} MB)')
else:
    raise FileNotFoundError('Video file missing or too small')
"
```

---

## Step 6: Present Result to the User

Provide the user with:
1. A clickable markdown file link to the generated video: `[final_video.mp4](file:///absolute/path/to/output/final_video.mp4)`.
2. A summary table showing scene breakdown, voiceover text, and durations.
3. Key specifications (Resolution, Aspect Ratio, Duration, FPS).
