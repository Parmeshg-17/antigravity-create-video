#!/usr/bin/env python3
"""
generate_video.py - Automated Video Generator for Google Antigravity
Synthesizes voiceover with edge-tts, generates dynamic 1080p visual cards/images,
applies Ken Burns pan/zoom motion, burns in captions, and compiles final MP4 video.
"""

import os
import sys
import json
import math
import shutil
import random
import asyncio
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Utility: Locate FFmpeg executable
# ---------------------------------------------------------------------------
def get_ffmpeg_binary():
    """Finds ffmpeg executable from PATH, imageio_ffmpeg, or common locations."""
    # 1. System PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 2. imageio_ffmpeg if installed
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # 3. Common Windows locations
    win_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
        Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
    ]
    for p in win_paths:
        if p.exists():
            return str(p)

    return "ffmpeg"


FFMPEG_BIN = get_ffmpeg_binary()

# ---------------------------------------------------------------------------
# Audio Duration Probing
# ---------------------------------------------------------------------------
def get_audio_duration(file_path):
    """Probes exact audio duration in seconds using ffmpeg."""
    cmd = [FFMPEG_BIN, "-i", str(file_path)]
    try:
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception as e:
        print(f"[Warning] Failed to probe duration via ffmpeg ({e}). Falling back to file estimation.")
    return 5.0  # safe fallback


# ---------------------------------------------------------------------------
# TTS Narration Synthesizer (Edge-TTS with Fallbacks)
# ---------------------------------------------------------------------------
async def synthesize_speech(text, voice, output_audio_path):
    """Synthesizes voiceover using edge-tts. Falls back to offline SAPI or silence if needed."""
    output_audio_path = Path(output_audio_path)
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_audio_path))
        if output_audio_path.exists() and output_audio_path.stat().st_size > 500:
            return True
    except Exception as err:
        print(f"[Warning] edge-tts error: {err}. Attempting fallback...")

    # Fallback for Windows: SAPI SpeechSynthesizer via PowerShell
    if sys.platform == "win32":
        try:
            ps_script = f"""
            Add-Type -AssemblyName System.Speech;
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
            $synth.SetOutputToWaveFile('{output_audio_path.with_suffix('.wav')}');
            $synth.Speak('{text.replace("'", " ")}');
            $synth.Dispose();
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True, capture_output=True)
            wav_path = output_audio_path.with_suffix('.wav')
            if wav_path.exists():
                # Convert wav to mp3
                subprocess.run([FFMPEG_BIN, "-y", "-i", str(wav_path), "-c:a", "libmp3lame", str(output_audio_path)], capture_output=True)
                wav_path.unlink(missing_ok=True)
                return True
        except Exception as e:
            print(f"[Warning] PowerShell SAPI fallback failed: {e}")

    # Ultimate fallback: Generate silent audio matching estimated reading speed (~3 words/sec)
    words = len(text.split())
    duration = max(3.0, words / 2.5)
    subprocess.run([
        FFMPEG_BIN, "-y", "-f", "lavfi", "-i",
        f"anullsrc=r=24000:cl=mono", "-t", str(duration),
        "-c:a", "libmp3lame", str(output_audio_path)
    ], capture_output=True)
    return True


# ---------------------------------------------------------------------------
# Graphics & Layout Helper Functions
# ---------------------------------------------------------------------------
def hex_to_rgb(hex_str, default=(30, 30, 60)):
    """Converts hex color string like #1E1B4B to (R, G, B) tuple."""
    if not hex_str or not isinstance(hex_str, str):
        return default
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])
    if len(hex_str) == 6:
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default


def get_default_font(size):
    """Loads a clean TrueType font or falls back gracefully to default PIL font."""
    font_names = [
        "arial.ttf", "Arial.ttf", "seguiemj.ttf", "segoeui.ttf", "calibri.ttf",
        "DejaVuSans.ttf", "Helvetica.ttf", "Roboto-Regular.ttf"
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    """Wraps text so lines fit neatly within max_width pixels."""
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        # Use getbbox or getlength
        try:
            w = font.getlength(test_line)
        except Exception:
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]

        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def create_gradient_image(width, height, color1, color2, direction="diagonal"):
    """Creates a high-resolution gradient canvas."""
    base = Image.new("RGB", (width, height), color1)
    top = Image.new("RGB", (width, height), color2)
    mask = Image.new("L", (width, height))
    mask_data = []

    for y in range(height):
        for x in range(width):
            if direction == "diagonal":
                val = int(255 * (x / width * 0.5 + y / height * 0.5))
            elif direction == "vertical":
                val = int(255 * (y / height))
            else:
                val = int(255 * (x / width))
            mask_data.append(min(255, max(0, val)))

    mask.putdata(mask_data)
    return Image.composite(top, base, mask)


def render_scene_base_card(scene, width, height, aspect_ratio):
    """Renders high-res base canvas for a scene: image or gradient card with badges & title."""
    image_path = scene.get("image_path")
    
    # 1. Background layer: custom image or gradient
    if image_path and os.path.isfile(image_path):
        try:
            bg = Image.open(image_path).convert("RGB")
            # Crop to aspect ratio then resize
            bg_w, bg_h = bg.size
            target_ratio = width / height
            cur_ratio = bg_w / bg_h
            if cur_ratio > target_ratio:
                new_w = int(bg_h * target_ratio)
                x_off = (bg_w - new_w) // 2
                bg = bg.crop((x_off, 0, x_off + new_w, bg_h))
            else:
                new_h = int(bg_w / target_ratio)
                y_off = (bg_h - new_h) // 2
                bg = bg.crop((0, y_off, bg_w, y_off + new_h))
            card = bg.resize((width, height), Image.Resampling.LANCZOS)
            # Add subtle dark vignette overlay for readability
            vignette = Image.new("RGBA", (width, height), (0, 0, 0, 70))
            card = card.convert("RGBA")
            card = Image.alpha_composite(card, vignette).convert("RGB")
        except Exception as e:
            print(f"[Warning] Failed to load image {image_path}: {e}. Using gradient card.")
            image_path = None

    if not image_path or not os.path.isfile(image_path):
        colors = scene.get("background_colors", ["#0F172A", "#1E293B"])
        c1 = hex_to_rgb(colors[0], (15, 23, 42))
        c2 = hex_to_rgb(colors[1] if len(colors) > 1 else colors[0], (30, 41, 59))
        card = create_gradient_image(width, height, c1, c2, direction="diagonal")
        draw = ImageDraw.Draw(card, "RGBA")

        # Subtle decorative geometric grid / circles
        accent_rgb = hex_to_rgb(scene.get("accent_color", "#38BDF8"), (56, 189, 248))
        circle_color = accent_rgb + (20,)
        draw.ellipse([width * 0.7, -height * 0.1, width * 1.3, height * 0.3], fill=circle_color)
        draw.ellipse([-width * 0.2, height * 0.7, width * 0.4, height * 1.2], fill=circle_color)

        # Draw decorative grid lines
        grid_color = (255, 255, 255, 10)
        step = width // 12
        for gx in range(0, width, step):
            draw.line([(gx, 0), (gx, height)], fill=grid_color, width=1)
        for gy in range(0, height, step):
            draw.line([(0, gy), (width, gy)], fill=grid_color, width=1)

    # 2. Text Content (Badge, Title, Subtitle)
    draw = ImageDraw.Draw(card, "RGBA")
    text_color = hex_to_rgb(scene.get("text_color", "#FFFFFF"), (255, 255, 255))
    accent_color = hex_to_rgb(scene.get("accent_color", "#38BDF8"), (56, 189, 248))

    is_vertical = aspect_ratio == "9:16"
    title_size = int(height * 0.048 if is_vertical else height * 0.065)
    sub_size = int(title_size * 0.55)
    badge_size = int(title_size * 0.38)

    title_font = get_default_font(title_size)
    sub_font = get_default_font(sub_size)
    badge_font = get_default_font(badge_size)

    # Center coordinates
    center_y = int(height * 0.40 if is_vertical else height * 0.42)
    max_text_w = int(width * 0.85)

    badge = scene.get("badge")
    title = scene.get("title", "")
    subtitle = scene.get("subtitle", "")

    # Render Badge Pill
    if badge:
        badge_text = str(badge).upper()
        bbox = badge_font.getbbox(badge_text)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        pad_x, pad_y = 16, 8
        bx1 = (width - bw) // 2 - pad_x
        by1 = center_y - int(title_size * 1.8)
        bx2 = bx1 + bw + pad_x * 2
        by2 = by1 + bh + pad_y * 2
        
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=12, fill=accent_color + (230,))
        draw.text(((width - bw) // 2, by1 + pad_y - 2), badge_text, fill=(15, 23, 42), font=badge_font)

    # Render Title with Word Wrapping
    title_lines = wrap_text(title, title_font, max_text_w)
    line_h = int(title_size * 1.25)
    total_title_h = len(title_lines) * line_h
    start_y = center_y - (total_title_h // 2)

    for i, line in enumerate(title_lines):
        bbox = title_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lx = (width - lw) // 2
        ly = start_y + i * line_h
        # Draw drop shadow
        draw.text((lx + 3, ly + 3), line, fill=(0, 0, 0, 160), font=title_font)
        draw.text((lx, ly), line, fill=text_color, font=title_font)

    # Render Subtitle
    if subtitle:
        sub_lines = wrap_text(subtitle, sub_font, max_text_w)
        sub_y = start_y + total_title_h + int(title_size * 0.4)
        for i, sline in enumerate(sub_lines):
            bbox = sub_font.getbbox(sline)
            slw = bbox[2] - bbox[0]
            slx = (width - slw) // 2
            sly = sub_y + i * int(sub_size * 1.3)
            draw.text((slx + 2, sly + 2), sline, fill=(0, 0, 0, 140), font=sub_font)
            draw.text((slx, sly), sline, fill=(226, 232, 240), font=sub_font)

    return card


def draw_burned_in_caption(frame, caption_text, width, height, aspect_ratio):
    """Draws a bold, high-contrast, centered subtitle pill at the bottom third."""
    if not caption_text:
        return frame

    draw = ImageDraw.Draw(frame, "RGBA")
    is_vertical = aspect_ratio == "9:16"
    cap_size = int(height * 0.032 if is_vertical else height * 0.042)
    cap_font = get_default_font(cap_size)

    max_w = int(width * 0.86)
    lines = wrap_text(caption_text, cap_font, max_w)
    if not lines:
        return frame

    line_h = int(cap_size * 1.3)
    total_h = len(lines) * line_h

    # Position at lower third
    bottom_y = int(height * 0.82 if is_vertical else height * 0.86)
    top_y = bottom_y - total_h

    # Draw rounded background pill
    pad_x, pad_y = 24, 12
    max_line_w = max(cap_font.getbbox(l)[2] - cap_font.getbbox(l)[0] for l in lines)
    pill_x1 = max(20, (width - max_line_w) // 2 - pad_x)
    pill_y1 = top_y - pad_y
    pill_x2 = min(width - 20, (width + max_line_w) // 2 + pad_x)
    pill_y2 = bottom_y + pad_y

    draw.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2], radius=16, fill=(0, 0, 0, 180))

    # Draw text
    for i, line in enumerate(lines):
        bbox = cap_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lx = (width - lw) // 2
        ly = top_y + i * line_h
        draw.text((lx + 2, ly + 2), line, fill=(0, 0, 0, 220), font=cap_font)
        draw.text((lx, ly), line, fill=(255, 255, 255, 255), font=cap_font)

    return frame


def ease_in_out(t):
    """Smooth cosine ease curve."""
    return 0.5 - 0.5 * math.cos(math.pi * t)


def render_scene_frames(base_img, motion_type, duration_sec, fps, target_w, target_h, caption_text, aspect_ratio):
    """Applies Ken Burns camera movement (pan/zoom) and burns in subtitles for each frame."""
    num_frames = int(round(duration_sec * fps))
    base_w, base_h = base_img.size

    # Ensure base canvas is pre-scaled by 1.25x for crisp zoom
    scale_factor = 1.25
    scaled_w = int(target_w * scale_factor)
    scaled_h = int(target_h * scale_factor)
    if base_img.size != (scaled_w, scaled_h):
        high_res = base_img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    else:
        high_res = base_img

    bw, bh = high_res.size

    for f_idx in range(num_frames):
        t = f_idx / max(1, num_frames - 1)
        e = ease_in_out(t)

        zoom = 1.05
        cx_ratio, cy_ratio = 0.5, 0.5
        offset_x, offset_y = 0.0, 0.0

        if motion_type == "zoom_in":
            zoom = 1.0 + 0.18 * e
        elif motion_type == "zoom_out":
            zoom = 1.18 - 0.18 * e
        elif motion_type == "pan_up":
            zoom = 1.12
            cy_ratio = 0.58 - 0.16 * e
        elif motion_type == "pan_down":
            zoom = 1.12
            cy_ratio = 0.42 + 0.16 * e
        elif motion_type == "pan_left":
            zoom = 1.12
            cx_ratio = 0.58 - 0.16 * e
        elif motion_type == "pan_right":
            zoom = 1.12
            cx_ratio = 0.42 + 0.16 * e
        elif motion_type == "shake":
            zoom = 1.08 + 0.03 * math.sin(f_idx * 0.2)
            shake_amp = 5.0
            offset_x = math.sin(f_idx * 1.2) * shake_amp + (random.random() - 0.5) * 2.0
            offset_y = math.cos(f_idx * 0.9) * shake_amp + (random.random() - 0.5) * 2.0

        # Calculate crop rectangle
        crop_w = bw / zoom
        crop_h = bh / zoom
        cx = bw * cx_ratio + offset_x
        cy = bh * cy_ratio + offset_y

        x1 = max(0, min(bw - crop_w, cx - crop_w / 2.0))
        y1 = max(0, min(bh - crop_h, cy - crop_h / 2.0))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        cropped = high_res.crop((int(x1), int(y1), int(x2), int(y2)))
        frame = cropped.resize((target_w, target_h), Image.Resampling.BILINEAR)

        # Burn in caption subtitle
        frame = draw_burned_in_caption(frame, caption_text, target_w, target_h, aspect_ratio)
        yield frame


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
async def build_video(storyboard_path, aspect_arg=None, output_arg=None, fps_arg=30, keep_temp=False):
    """Compiles complete video from storyboard JSON."""
    sb_file = Path(storyboard_path).resolve()
    if not sb_file.exists():
        raise FileNotFoundError(f"Storyboard not found at: {sb_file}")

    with open(sb_file, "r", encoding="utf-8") as f:
        sb = json.load(f)

    # Resolve aspect ratio & dimensions
    aspect = aspect_arg or sb.get("aspect_ratio", "16:9")
    if aspect == "9:16":
        width, height = 1080, 1920
    else:
        aspect = "16:9"
        width, height = 1920, 1080

    fps = fps_arg or sb.get("fps", 30)
    fade_frames = sb.get("transition_frames", 10)
    default_voice = sb.get("voice", "en-US-ChristopherNeural")

    out_file = Path(output_arg or sb.get("output", "output/final_video.mp4")).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = out_file.parent / "temp_video_build"
    temp_dir.mkdir(parents=True, exist_ok=True)

    scenes = sb.get("scenes", [])
    if not scenes:
        raise ValueError("Storyboard must contain at least one scene in 'scenes' array.")

    print(f"\n========================================================")
    print(f"🎬 Antigravity Video Generator")
    print(f"Title: {sb.get('title', 'Untitled')}")
    print(f"Aspect Ratio: {aspect} ({width}x{height}) @ {fps} FPS")
    print(f"Total Scenes: {len(scenes)}")
    print(f"Output File: {out_file}")
    print(f"========================================================\n")

    # Step 1: Synthesize Audio & Determine Scene Durations
    print("[1/3] 🎙️ Synthesizing voiceover narrations with Edge-TTS...")
    audio_files = []
    scene_durations = []

    for i, sc in enumerate(scenes):
        scene_id = sc.get("id", i + 1)
        narration = sc.get("narration") or sc.get("text", "")
        voice = sc.get("voice", default_voice)
        audio_path = temp_dir / f"scene_{scene_id}_audio.mp3"

        if narration.strip():
            print(f"  - Scene {scene_id}: Synthesizing voiceover ({voice})...")
            await synthesize_speech(narration, voice, audio_path)
            duration = get_audio_duration(audio_path)
        else:
            # Silent scene with configured duration
            duration = float(sc.get("duration", 4.0))
            subprocess.run([
                FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(duration), "-c:a", "libmp3lame", str(audio_path)
            ], capture_output=True)

        # Add small pacing buffer (0.35s) so scene doesn't cut off abruptly
        scene_dur = max(duration + 0.35, float(sc.get("duration", 0)))
        audio_files.append(audio_path)
        scene_durations.append(scene_dur)
        print(f"    Duration: {scene_dur:.2f}s")

    # Concatenate all audio files into a unified soundtrack
    concat_txt = temp_dir / "audio_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for a_path in audio_files:
            # Escape path for ffmpeg concat
            clean_p = str(a_path).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    full_audio_mp3 = temp_dir / "soundtrack.mp3"
    concat_cmd = [
        FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt), "-c:a", "libmp3lame", "-q:a", "2",
        str(full_audio_mp3)
    ]
    subprocess.run(concat_cmd, check=True, capture_output=True)
    total_audio_sec = get_audio_duration(full_audio_mp3)
    print(f"\n[Soundtrack ready] Total duration: {total_audio_sec:.2f}s\n")

    # Step 2: Render Visual Frames & Compile Video
    print("[2/3] 🎨 Rendering 1080p visual cards, Ken Burns motion, and captions...")
    scene_frames_count = [int(round(d * fps)) for d in scene_durations]
    total_video_frames = sum(scene_frames_count)

    # Pre-render base canvas cards for each scene (1.25x scale for clean zoom)
    scale = 1.25
    buffer_w = int(width * scale)
    buffer_h = int(height * scale)
    base_cards = []

    for i, sc in enumerate(scenes):
        card = render_scene_base_card(sc, buffer_w, buffer_h, aspect)
        base_cards.append(card)

    # Frame generator with smooth crossfades
    def frame_stream():
        scene_starts = []
        curr = 0
        for nf in scene_frames_count:
            scene_starts.append(curr)
            curr += nf

        # Cache generators
        gen_cache = []
        for i, sc in enumerate(scenes):
            dur = scene_durations[i]
            motion = sc.get("motion", "zoom_in")
            caption = sc.get("caption", sc.get("narration", ""))
            gen = list(render_scene_frames(
                base_cards[i], motion, dur, fps, width, height, caption, aspect
            ))
            gen_cache.append(gen)

        for total_f in range(total_video_frames):
            s_idx = 0
            for idx, start_f in enumerate(scene_starts):
                if total_f >= start_f:
                    s_idx = idx

            local_f = total_f - scene_starts[s_idx]
            current_scene_frames = gen_cache[s_idx]
            frame_img = current_scene_frames[min(local_f, len(current_scene_frames) - 1)]

            # Cross-dissolve transition between scenes
            if local_f >= (len(current_scene_frames) - fade_frames) and s_idx < len(scenes) - 1:
                fade_idx = local_f - (len(current_scene_frames) - fade_frames)
                ratio = (fade_idx + 1) / (fade_frames + 1)
                next_frame = gen_cache[s_idx + 1][0]
                frame_img = Image.blend(frame_img, next_frame, ratio)

            yield frame_img

    # Step 3: Stream frames directly into FFmpeg H.264 encoder
    print(f"[3/3] 🚀 Encoding MP4 video with FFmpeg ({total_video_frames} frames)...")
    ffmpeg_cmd = [
        FFMPEG_BIN,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",                     # video pipe stdin
        "-i", str(full_audio_mp3),     # audio soundtrack
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_file)
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rendered = 0
    for frame in frame_stream():
        raw_bytes = frame.tobytes()
        proc.stdin.write(raw_bytes)
        rendered += 1
        if rendered % 90 == 0 or rendered == total_video_frames:
            pct = (rendered / total_video_frames) * 100
            print(f"  Rendering progress: {rendered}/{total_video_frames} frames ({pct:.1f}%)")

    proc.stdin.close()
    stdout, stderr = proc.communicate()

    if proc.returncode != 0:
        print("[Error] FFmpeg compilation failed:", stderr.decode("utf-8", errors="ignore"))
        sys.exit(1)

    # Cleanup temp directory
    if not keep_temp and temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

    file_size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"\n🎉 SUCCESS: Video rendered successfully!")
    print(f"📁 File: {out_file}")
    print(f"📊 Size: {file_size_mb:.2f} MB")
    print(f"⏱️ Length: {total_audio_sec:.2f}s | Resolution: {width}x{height}\n")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Antigravity Video Generator")
    parser.add_argument("--storyboard", default="output/storyboard.json", help="Path to storyboard JSON file")
    parser.add_argument("--aspect", choices=["16:9", "9:16"], default=None, help="Force aspect ratio (16:9 or 9:16)")
    parser.add_argument("--output", default="output/final_video.mp4", help="Output MP4 file path")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--keep-temp", action="store_true", help="Preserve intermediate temporary files")

    args = parser.parse_args()
    asyncio.run(build_video(
        storyboard_path=args.storyboard,
        aspect_arg=args.aspect,
        output_arg=args.output,
        fps_arg=args.fps,
        keep_temp=args.keep_temp
    ))


if __name__ == "__main__":
    main()
