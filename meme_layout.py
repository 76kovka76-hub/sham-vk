"""Deterministic, varied, readable SHAM meme typography.

Six visual caption treatments while keeping the generated scene visible.
Russian text is rendered precisely by Pillow; never ask SDXL to spell it.
"""
from datetime import date
from PIL import Image, ImageDraw, ImageOps

LAYOUTS = ("gradient", "editorial", "darkroom", "film", "neon", "papercut")


def layout_for_slot(slot):
    try:
        day, hour, quarter = slot.rsplit("-", 2)
        ordinal = date.fromisoformat(day).toordinal() * 96
        h, q = int(hour), int(quarter)
        if len(hour) != 2 or len(quarter) != 2 or not 0 <= h < 24 or not 0 <= q < 4:
            raise ValueError("Invalid time")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Invalid SHAM layout slot") from exc
    return LAYOUTS[(ordinal + h * 4 + q) % len(LAYOUTS)]


def render_meme(source, post, slot, font, centered_text):
    canvas = ImageOps.fit(
        source, (1080, 1080), method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.48)).convert("RGBA")
    overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    layout = layout_for_slot(slot)
    top_color = (255, 255, 255, 255)
    bottom_color = (255, 236, 73, 255)

    if layout == "gradient":
        for y in range(270):
            strength = max(0, int(218 * (1 - y / 280)))
            d.line((0, y, 1079, y), fill=(3, 6, 12, strength))
        for y in range(793, 1080):
            strength = min(248, int(170 + 75 * (y - 793) / 287))
            d.line((0, y, 1079, y), fill=(3, 6, 12, strength))
    elif layout == "editorial":
        d.rectangle((0, 0, 1080, 255), fill=(14, 17, 25, 245))
        d.rectangle((0, 794, 1080, 1080), fill=(14, 17, 25, 245))
        d.rectangle((28, 252, 1052, 260), fill=(255, 202, 70, 255))
        bottom_color = (255, 202, 70, 255)
    elif layout == "darkroom":
        d.rectangle((0, 0, 1080, 254), fill=(4, 4, 5, 237))
        d.rectangle((0, 792, 1080, 1080), fill=(4, 4, 5, 238))
        d.rectangle((12, 12, 1068, 1068), outline=(235, 235, 230, 130), width=6)
        bottom_color = (235, 235, 230, 255)
    elif layout == "film":
        d.rectangle((0, 0, 1080, 261), fill=(13, 20, 28, 246))
        d.rectangle((0, 786, 1080, 1080), fill=(13, 20, 28, 246))
        d.rectangle((24, 258, 1056, 263), fill=(220, 223, 227, 155))
        d.rectangle((24, 783, 1056, 788), fill=(220, 223, 227, 155))
        bottom_color = (230, 239, 248, 255)
    elif layout == "neon":
        d.rounded_rectangle((12, 7, 1068, 262), radius=28, fill=(9, 6, 32, 244))
        d.rounded_rectangle((12, 788, 1068, 1073), radius=28, fill=(9, 6, 32, 244))
        d.rounded_rectangle((12, 788, 1068, 1073), radius=28,
                            outline=(230, 67, 213, 238), width=5)
        bottom_color = (244, 122, 234, 255)
    else:  # papercut: deliberately contrasting physical collage strips
        d.rectangle((0, 0, 1080, 256), fill=(23, 29, 33, 248))
        d.rectangle((0, 788, 1080, 1080), fill=(23, 29, 33, 248))
        d.polygon([(0, 244), (160, 250), (360, 242), (560, 251),
                   (770, 246), (1080, 254), (1080, 259), (0, 259)],
                  fill=(248, 238, 214, 215))
        d.polygon([(0, 786), (260, 780), (500, 789), (720, 784),
                   (930, 788), (1080, 780), (1080, 797), (0, 797)],
                  fill=(248, 238, 214, 215))
        bottom_color = (250, 224, 149, 255)

    image = Image.alpha_composite(canvas, overlay)
    d = ImageDraw.Draw(image)
    # Two dedicated wide text zones; overflow fails rather than scaling tiny.
    centered_text(d, post["top"], 16, 243, top_color, 72)
    centered_text(d, post["bottom"], 805, 1029, bottom_color, 72)
    d.text((540, 1054), "SHAM", font=font(29), anchor="mm",
           fill=(237, 237, 235, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return image.convert("RGB"), layout
