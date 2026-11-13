"""Weekly SHAM top-three poster from verified non-demo engagement only.

A weekly recap is not a duplicate of any individual meme: three original
SHAM jokes appear as a ranked digest with links to the actual VK posts.
Never publish if analytics is unavailable, demo, or unverifiable.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sham_insights import fetch_best_analytics, summarize


def _font(n):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", n)


def _wrapped(draw, text, face, limit):
    result, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if line and draw.textbbox((0, 0), test, font=face)[2] > limit:
            result.append(line)
            line = word
        else:
            line = test
    if line:
        result.append(line)
    return result


def draw_top(top, path):
    if len(top) < 3 or len({str(r.get("post_id")) for r in top[:3]}) < 3:
        raise ValueError("Need at least three different verified posts")
    image = Image.new("RGB", (1080, 1080), (18, 24, 33))
    draw = ImageDraw.Draw(image)
    draw.text((60, 42), "SHAM", font=_font(72), fill=(255, 233, 115))
    draw.text((60, 135), "ТОП-3 МЕМА НЕДЕЛИ", font=_font(47), fill=(255, 255, 255))
    for n, post in enumerate(top[:3], 1):
        y = 232 + (n - 1) * 262
        draw.rounded_rectangle((46, y, 1034, y + 238), radius=22,
                               fill=(37 + n * 5, 42 + n * 5, 54 + n * 3))
        draw.text((78, y + 18), str(n), font=_font(84), fill=(255, 220, 92))
        text = str(post.get("caption", "")).strip()
        face = _font(35)
        lines = _wrapped(draw, text, face, 820)
        if len(lines) > 4:
            face = _font(28)
            lines = _wrapped(draw, text, face, 820)
        if len(lines) > 5:
            raise ValueError("Weekly meme text not readable without excessive clipping")
        for index, line in enumerate(lines):
            draw.text((179, y + 24 + index * (face.size + 8)), line, font=face,
                      fill=(250, 250, 250))
    draw.text((80, 1031), "Полные мемы — в постах сообщества", font=_font(24),
              fill=(230, 232, 235))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
    return path


def weekly_top(*, preview=False, now=None):
    now = now or datetime.now(timezone.utc)
    if not preview and now.isoweekday() != 7:
        return {"status": "skipped", "reason": "not_sunday"}
    from main import get_state
    state = get_state()
    summary = summarize(state, fetch_best_analytics(state, now=now))
    verified = [p for p in summary["top"]
                if p.get("vk_url", "").startswith("https://vk.")]
    if summary["status"] != "ok" or len(verified) < 3:
        return {"status": "skipped", "reason": "insufficient_verified_metrics",
                "count": len(verified)}
    target = draw_top(verified, Path("output/sham_weekly_top.png"))
    caption = ("🔥 SHAM: три лучших мема недели по настоящим реакциям.\n"
               + "\n".join(f"{i}. {p['vk_url']}"
                           for i, p in enumerate(verified[:3], 1))
               + "\n#SHAM #мемы #топнедели")
    digest = {"status": "preview", "links": [p["vk_url"] for p in verified[:3]],
              "image": str(target), "caption": caption}
    if not preview and os.getenv("SHAM_WEEKLY_PUBLISH", "").lower() in ("yes", "1", "true"):
        from vedismm_publisher import publish_vedismm
        week = now.isocalendar()
        slot = f"weekly-{week.year}-W{week.week:02d}"
        result = publish_vedismm(target, caption, slot)
        digest["status"] = "published" if result["status"] == "published" else "queued"
        digest["vedismm_post_id"] = result["post_id"]
        digest["vk_url"] = result.get("url", "")
    Path("output/sham_weekly_top.json").write_text(
        json.dumps(digest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return digest


if __name__ == "__main__":
    print("SHAM_WEEKLY_TOP:", weekly_top())
