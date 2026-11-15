# Storyboard JSON Schema and Reference

This document defines the schema for `output/storyboard.json` used by the `create-video` skill to render complete MP4 videos with AI voiceover, captions, and motion graphics.

---

## Schema Overview

The storyboard JSON file contains global video configurations and an ordered list of `scenes`.

### Top-Level Properties

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `title` | String | Yes | `""` | Project title or topic. |
| `aspect_ratio` | String | No | `"16:9"` | Aspect ratio: `"16:9"` (1920x1080 landscape) or `"9:16"` (1080x1920 vertical). |
| `voice` | String | No | `"en-US-ChristopherNeural"` | Default Edge-TTS voice model for narration across all scenes. |
| `fps` | Integer | No | `30` | Video frame rate. Default is 30 fps. |
| `transition_frames`| Integer | No | `10` | Crossfade transition duration in frames between consecutive scenes. |
| `scenes` | Array | Yes | - | Ordered array of scene objects. |

---

### Scene Object Properties

Each scene in the `scenes` array represents a distinct visual slide and spoken narration:

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer / String | Yes | - | Unique scene identifier (e.g. `1`, `"scene_1"`). |
| `title` | String | Yes | `""` | Bold on-screen headline displayed prominently on the card. |
| `subtitle` | String | No | `""` | Supporting on-screen subtitle or bullet takeaway. |
| `narration` | String | Yes | `""` | Exact voiceover text synthesized by Edge-TTS. |
| `voice` | String | No | Inherits global | Scene-specific Edge-TTS voice override (e.g., for multi-speaker dialog). |
| `duration` | Number | No | Dynamic | Minimum scene duration in seconds. If audio narration is longer, video length automatically expands to match audio. |
| `image_path` | String | No | `null` | Path to an existing background image (e.g., generated 2D art, screenshot, photo). |
| `motion` | String | No | `"zoom_in"` | Camera motion: `"zoom_in"`, `"zoom_out"`, `"pan_up"`, `"pan_down"`, `"pan_left"`, `"pan_right"`, or `"shake"`. |
| `background_colors`| Array[String] | No | `["#1E1B4B", "#312E81"]` | Hex color codes for the background gradient (2 or 3 colors). |
| `text_color` | String | No | `"#FFFFFF"` | Hex color code for title and subtitle text. |
| `accent_color` | String | No | `"#F59E0B"` | Hex color code for badges, borders, or highlights. |
| `badge` | String | No | `"STEP 01"` | Small category pill tag rendered above the title. |

---

## Edge-TTS Voice Recommendations

Common natural AI voices available without API keys:

* **English (US):**
  * `en-US-ChristopherNeural` (Male, authoritative, explainer / tech)
  * `en-US-JennyNeural` (Female, friendly, conversational)
  * `en-US-GuyNeural` (Male, casual, energetic)
  * `en-US-AriaNeural` (Female, clear, professional)
* **English (UK):**
  * `en-GB-SoniaNeural` (Female, warm)
  * `en-GB-RyanNeural` (Male, polished)
* **Hindi (India):**
  * `hi-IN-MadhurNeural` (Male, clear, narrative)
  * `hi-IN-SwaraNeural` (Female, expressive, broadcast)

---

## Complete Working Example

Below is a complete `output/storyboard.json` example configured for a 9:16 vertical short:

```json
{
  "title": "5 Laws of Human Psychology",
  "aspect_ratio": "9:16",
  "voice": "en-US-ChristopherNeural",
  "fps": 30,
  "transition_frames": 12,
  "scenes": [
    {
      "id": 1,
      "badge": "FACT 01",
      "title": "The Pratfall Effect",
      "subtitle": "Flaws make you more likable",
      "narration": "Have you ever made a silly mistake in front of others? Science proves that competent people become more likable when they show minor imperfections.",
      "motion": "zoom_in",
      "background_colors": ["#0f172a", "#1e293b"],
      "text_color": "#ffffff",
      "accent_color": "#38bdf8"
    },
    {
      "id": 2,
      "badge": "FACT 02",
      "title": "The Pygmalion Effect",
      "subtitle": "High expectations drive high performance",
      "narration": "When leaders believe someone will succeed, that person unconsciously rises to meet those expectations. Believe in people and watch them grow.",
      "motion": "pan_up",
      "background_colors": ["#1e1b4b", "#4338ca"],
      "text_color": "#ffffff",
      "accent_color": "#a855f7"
    },
    {
      "id": 3,
      "badge": "TAKEAWAY",
      "title": "Master Your Mind",
      "subtitle": "Knowledge is power",
      "narration": "Understanding these human psychology principles gives you an unfair advantage in life and leadership. Follow for more daily insights.",
      "motion": "zoom_out",
      "background_colors": ["#064e3b", "#047857"],
      "text_color": "#ffffff",
      "accent_color": "#34d399"
    }
  ]
}
```
