# 🎬 Antigravity Create Video Skill

> A production-ready **Google Antigravity** skill to generate complete, high-definition MP4 videos (with natural AI voiceover, burned-in subtitles, and smooth animated motion cards) directly from text prompts, scripts, or project topics.

---

## ✨ Features

- **Automated AI Voiceover**: Uses Microsoft Edge-TTS for realistic, high-quality speech without requiring paid API keys or subscriptions.
- **Dynamic Storyboard Execution**: Automatically translates any topic into structured scenes, paced narration, on-screen titles, and visual aesthetics.
- **1080p Resolution & Multiple Formats**: Supports both **16:9 Landscape** (`1920x1080` for YouTube/presentations) and **9:16 Vertical** (`1080x1920` for YouTube Shorts, Instagram Reels, and TikTok).
- **Cinematic Motion**: Smooth Ken Burns pan & zoom effects (`zoom_in`, `zoom_out`, `pan_up`, `pan_down`, `shake`).
- **Clean Burned-In Captions**: High-contrast, centered subtitle pills positioned cleanly at the lower third for maximum mobile readability.
- **Seamless Scene Transitions**: Smooth crossfade dissolve between slides.
- **Custom Visuals**: Supports optional background images or auto-generates sleek gradient cards with modern typography.

---

## 🚀 Example Antigravity Prompts

Once installed, simply ask Antigravity in your chat:

- *"Create a 30-second YouTube Short explaining 3 psychological tricks to improve focus."*
- *"Generate a 16:9 explainer video about how Docker containers work with voiceover and captions."*
- *"Make an Instagram Reel about the life of Nikola Tesla with dramatic music pacing."*
- *"Produce a 4-scene video summary of our project's architecture."*

---

## 📦 Quick Start (Local Workspace)

### 1. Clone the Repository
```bash
git clone https://github.com/Parmeshg-17/antigravity-create-video.git
cd antigravity-create-video
```

### 2. Install Dependencies
Make sure you have Python 3.9+ and FFmpeg installed, then install the Python dependencies:

```bash
pip install -r requirements.txt
```

> **FFmpeg Note**: If `ffmpeg` is not already installed on your system, install it via:
> - **Windows**: `winget install Gyan.FFmpeg` or `choco install ffmpeg`
> - **macOS**: `brew install ffmpeg`
> - **Ubuntu/Debian**: `sudo apt update && sudo apt install -y ffmpeg`
>
> *(Note: The included `imageio-ffmpeg` package also provides an automatic bundled binary fallback).*

---

## 🌐 Global Installation (Available Across All Projects)

To make `/create-video` available anywhere in Antigravity regardless of what folder you have open, copy the skill folder to your global Antigravity config directory:

### On Windows (PowerShell):
```powershell
# Create global skills directory if it does not exist
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\config\skills\create-video"

# Copy skill files to global directory
Copy-Item -Recurse -Force ".agents\skills\create-video\*" "$env:USERPROFILE\.gemini\config\skills\create-video\"
```

### On macOS / Linux (Bash):
```bash
# Create global skills directory if it does not exist
mkdir -p ~/.gemini/config/skills/create-video

# Copy skill files to global directory
cp -r .agents/skills/create-video/* ~/.gemini/config/skills/create-video/
```

Once copied, Antigravity will automatically recognize the `create-video` skill in any session!

---

## 🛠️ How It Works Under the Hood

```
User Prompt
    │
    ▼
Antigravity Agent (triggers create-video skill)
    │
    ▼
Generates `output/storyboard.json` (scenes, narrations, colors, motion)
    │
    ▼
Executes `.agents/skills/create-video/scripts/generate_video.py`
    ├── Synthesizes voiceovers with edge-tts
    ├── Probes exact audio durations
    ├── Renders 1080p high-resolution frame cards with Pillow
    ├── Applies Ken Burns pan/zoom and dynamic subtitles
    └── Streams RGB frames directly into FFmpeg H.264 / AAC encoder
    │
    ▼
Outputs `output/final_video.mp4`
```

---

## 📂 Repository Structure

```
.
├── .agents/
│   └── skills/
│       └── create-video/
│           ├── SKILL.md                          # Antigravity skill definition & agent instructions
│           ├── scripts/
│           │   └── generate_video.py             # Core Python video compiler script
│           └── references/
│               └── storyboard_schema.md          # Storyboard JSON specification and examples
├── requirements.txt                              # Python package dependencies
├── README.md                                     # Documentation and setup guide
└── .gitignore                                    # Git ignore rules for video renders & caches
```

---

## 🧪 Testing the Video Generator Directly (CLI)

You can also run the generator standalone from your terminal:

```bash
# Generate video from a storyboard in 9:16 vertical format
python .agents/skills/create-video/scripts/generate_video.py --storyboard output/storyboard.json --aspect 9:16 --output output/final_video.mp4

# Generate video in 16:9 landscape format
python .agents/skills/create-video/scripts/generate_video.py --storyboard output/storyboard.json --aspect 16:9 --output output/final_video.mp4
```

---

## 📄 License

MIT License. Free to use, modify, and distribute for personal and commercial projects.
