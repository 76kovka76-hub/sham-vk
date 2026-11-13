"""SHAM visual direction: rotate across photographic, experimental, and illustrated media.

The style is deterministic for a UTC 15-minute slot, so retries reproduce
the same prompt. There is intentionally no 92-anime/4-photo quota.
"""
from datetime import date

STYLE_PROMPTS = {
    "realistic": "Hyperrealistic candid editorial photograph, natural skin and light, documentary color grading, believable physical objects.",
    "phone_photo": "Unposed handheld smartphone photograph, spontaneous candid snapshot, slight natural camera imperfection, lifelike everyday scene.",
    "cinematic": "Photorealistic cinematic movie still, atmospheric lighting, striking composition, narrative visual storytelling.",
    "flash_photo": "Realistic direct-flash party photography, harsh flash, natural imperfections, ridiculous candid moment.",
    "photojournalism": "Documentary photojournalism shot, believable spontaneous scene, detailed everyday surroundings, authentic emotion.",
    "street_photo": "35mm street photography, believable public place, human-scale environment, observational comedy.",
    "film_noir": "Black-and-white film noir photography, real photographed actors, hard shadows, crime-film mood applied to absurd comedy.",
    "vintage_photo": "Faded vintage color photograph from the 1970s, realistic analog film grain, retro clothes and setting.",
    "polaroid": "Authentic instant-film style photograph, slightly washed colors, physical photographic imperfection, candid comic scene.",
    "vhs_still": "Realistic camcorder VHS footage still, retro television video texture, believable photographed scene, unexpected absurd action.",
    "security_camera": "Realistic security CCTV freeze-frame, wide surveillance angle, lifelike location, odd physical comedy caught on camera.",
    "mockumentary": "Photorealistic mockumentary TV frame, deadpan absurd situation treated as a serious documentary, expressive realistic people.",
    "tabloid_photo": "Realistic staged tabloid-news photograph, dramatic everyday disaster, absurd public-interest photo framing, without readable signs.",
    "sports_photo": "Photorealistic sports-action photo applied to a trivial everyday challenge, energetic frozen movement, telephoto look.",
    "fashion_photo": "Realistic high-end fashion editorial photography featuring an absurd ordinary situation, authentic materials and lighting.",
    "macro_photo": "Detailed photorealistic macro photography of miniature absurd scene, tactile real-world surfaces, playful depth of field.",
    "miniature_photo": "Photograph of intricately built miniature diorama with physical real-world textures, practical props, human-scale comedy made tiny.",
    "photomontage": "Deliberately ridiculous photorealistic cut-and-paste composite, mismatched photographic objects and absurd visual proportions.",
    "surreal_photo": "Dreamlike impossible but photorealistic image, real photographic surfaces and uncanny absurd visual juxtaposition.",
    "practical_effects": "Photograph of practical special effects and physical props on a film set, believable textures, wild slapstick.",
    "retro_advert": "1960s retro magazine advertisement photograph, real models and absurd household product demonstration, no printed lettering.",
    "3d_render": "High-quality physically based 3D render, detailed tactile materials, cinematic product-quality lighting, surreal visual joke.",
    "claymation": "Stop-motion scene made of actual sculpted clay puppets, fingerprints and tabletop sets visible, absurd physical comedy.",
    "paper_collage": "Handmade cut-paper collage mixed with photographic clippings and torn edges, bold absurd juxtaposition.",
    "graphic_novel": "Expressive graphic-novel panel, dramatic ink and halftone shading, visual action clearer than decorative detail.",
    "watercolor": "Lively expressive watercolor illustration, loose painted washes and exaggerated everyday comedy.",
    "oil_painting": "Classical oil painting with tactile brushwork portraying a modern absurd situation, dramatic museum-like composition.",
    "pencil_sketch": "Loose expressive graphite pencil sketch, intentionally rough hand drawing, clear physical action and lively faces.",
    "pixel_art": "Detailed original pixel-art game screenshot style, coherent readable scene and funny physical action, no UI text.",
    "anime": "Polished Japanese anime comedy frame with expressive animation acting, detailed background, no repetitive generic portrait.",
    "comic_strip": "Original western comic-book panel, bold shapes and clear acting, one focused slapstick scene, no speech balloons.",
}

PHOTO_STYLES = frozenset({
    "realistic", "phone_photo", "cinematic", "flash_photo", "photojournalism",
    "street_photo", "film_noir", "vintage_photo", "polaroid", "vhs_still",
    "security_camera", "mockumentary", "tabloid_photo", "sports_photo",
    "fashion_photo", "macro_photo", "miniature_photo", "photomontage",
    "surreal_photo", "practical_effects", "retro_advert",
})
STYLE_ORDER = tuple(STYLE_PROMPTS)
assert len(STYLE_ORDER) == len(set(STYLE_ORDER)) >= 28


def style_for_slot(slot: str) -> str:
    """Rotate all visual genres with zero adjacent repeats and rare anime."""
    try:
        day_text, h_text, q_text = slot.rsplit("-", 2)
        day = date.fromisoformat(day_text)
        hour, quarter = int(h_text), int(q_text)
        if len(h_text) != 2 or len(q_text) != 2 or not 0 <= hour < 24 or not 0 <= quarter < 4:
            raise ValueError("Invalid UTC slot")
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"Bad SHAM slot: {slot!r}") from exc
    absolute_quarter = day.toordinal() * 96 + hour * 4 + quarter
    return STYLE_ORDER[absolute_quarter % len(STYLE_ORDER)]
