"""Motion meme previews built from an already QA-approved SHAM image.

The joke's punchline is revealed over a few frames. No auto-upload to VK:
VediSMM/video support must be validated separately to protect the PNG queue.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageOps


def reveal_frames(source, *, size=720):
    with Image.open(source) as img:
        full = ImageOps.fit(img.convert("RGB"), (size, size),
                            method=Image.Resampling.LANCZOS)
    # Each frame keeps the same art; it reveals the original Cyrillic ending.
    # The final hold is long enough to read.
    out = []
    for visibility in (0.0, .0, .14, .40, .66, .87, 1.0, 1.0, 1.0, 1.0):
        frame = full.copy()
        if visibility < 1:
            draw = ImageDraw.Draw(frame)
            y0, y1 = int(size * .746), int(size * .955)
            cover_from = y0 + int((y1 - y0) * visibility)
            if cover_from <= y1:
                draw.rectangle((0, cover_from, size, y1),
                               fill=(17, 20, 26))
        out.append(frame)
    return out


def make_motion_previews(png, out_dir, *, render_mp4=True):
    png, out_dir = Path(png), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = reveal_frames(png)
    gif = out_dir / "sham_reveal.gif"
    duration = [300, 250, 220, 220, 220, 220, 500, 500, 500, 700]
    frames[0].save(gif, format="GIF", save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True, disposal=2)
    result = {"gif": str(gif), "gif_frames": len(frames), "mp4": None}
    encoder = shutil.which("ffmpeg")
    if not render_mp4 or not encoder:
        return result
    with tempfile.TemporaryDirectory(prefix="sham_video_") as tmp:
        folder = Path(tmp)
        for i, frame in enumerate(frames):
            frame.save(folder / f"frame_{i:03d}.png")
        target = out_dir / "sham_reveal.mp4"
        cmd = [encoder, "-hide_banner", "-loglevel", "error", "-y",
               "-framerate", "3", "-i", str(folder / "frame_%03d.png"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", str(target)]
        try:
            subprocess.run(cmd, check=True, timeout=65,
                           capture_output=True)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return result
        if target.exists() and target.stat().st_size > 10000:
            result["mp4"] = str(target)
    return result


if __name__ == "__main__":
    from main import OUT
    print(make_motion_previews(OUT / "sham_meme.png", OUT))
