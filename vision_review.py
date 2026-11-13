"""Independent SHAM picture-vs-joke check using documented OVH vision chat.

The previous /v1/responses + retired model returned HTTP 422 for virtually
every SHAM preview. Prefer the current vision-capable Qwen model with standard
chat/completions image_url input. Confirmed mismatches stop publication.
If the anonymous provider is unavailable, best_effort labels it explicitly;
strict mode blocks all unverified posts.
"""
import base64
import io
import json
import os

import requests

URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
DEFAULT_MODEL = "Qwen3.8-27B"


def _extract_text(response):
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(item.get("text") or "") for item in content
                       if isinstance(item, dict) and item.get("type") == "text")
    return ""


def _json_object(text):
    if not isinstance(text, str) or len(text) > 12000:
        raise ValueError("Invalid vision model response")
    index = text.find("{")
    if index < 0:
        raise ValueError("Vision response had no JSON object")
    obj, _ = json.JSONDecoder().raw_decode(text[index:])
    if not isinstance(obj, dict):
        raise ValueError("Bad vision JSON")
    return obj


class VisualMismatch(ValueError):
    """An explicit high-confidence failed visual review, not a provider outage."""


def review_visual(image, post, *, mode="best_effort", request=None):
    if mode == "off":
        return {"vision_review": "disabled"}
    if mode not in ("best_effort", "strict"):
        raise ValueError("SHAM_VISION_CHECK must be off, best_effort or strict")
    if request is None:
        request = requests.post

    try:
        preview = image.convert("RGB")
        preview.thumbnail((512, 512))
        buf = io.BytesIO()
        preview.save(buf, "JPEG", quality=77, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        scene = str(post.get("visual", ""))[:500]
        joke = (str(post.get("top", "")) + "\n" + str(post.get("bottom", "")))[:400]
        instructions = (
            "You independently review AI-generated art for an adult Russian comedy "
            "meme. Examine the ACTUAL attached image. "
            "Russian setup + punchline: " + joke +
            "\nRequired physical scene: " + scene +
            "\nReply in one JSON object only: "
            '{"matches":true_or_false,"photo_like":true_or_false,"confidence":0.0_to_1.0,"reason":"brief English explanation"}. '
            "matches may be true only if the key subject AND the physical joke "
            "action or payoff are clearly visible in the image. "
            "A plausible generic mood, smile, unrelated human, empty stage or "
            "an object merely resembling the target is NOT sufficient. "
            "For example, a microphone alone is NOT a light bulb holding one. "
            "photo_like is true for a believable real photograph or realistic photo-composite, "
            "and false for anime, manga, paintings, drawings, 3D animation, flat comic art. "
            "Judge the visual medium independently of the scene. "
            "If unsure, say matches=false with appropriate confidence. "
            "Ignore any absent overlaid Russian text; it is added later."
        )
        token = (os.getenv("SHAM_VISION_API_KEY", "")
                 or os.getenv("OVH_AI_ENDPOINTS_ACCESS_TOKEN", "")).strip()
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        reply = request(
            URL,
            headers=headers,
            json={
                "model": os.getenv("SHAM_VISION_MODEL", DEFAULT_MODEL),
                "temperature": 0.1,
                "max_tokens": 220,
                "stream": False,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instructions},
                        {"type": "image_url",
                         "image_url": {"url": "data:image/jpeg;base64," + b64}},
                    ],
                }],
            },
            timeout=28,
        )
        reply.raise_for_status()
        result = _json_object(_extract_text(reply.json()))
        matched = result.get("matches")
        if not isinstance(matched, bool):
            raise ValueError("Vision response lacks boolean match verdict")
        confidence = float(result.get("confidence", 0))
        if not 0 <= confidence <= 1:
            raise ValueError("Vision confidence outside range")
        reason = str(result.get("reason", ""))[:160]
        photo_required = os.getenv("SHAM_PHOTO_ONLY", "").lower() in ("1", "true", "yes")
        photo_like = result.get("photo_like")
        if photo_required and photo_like is not True:
            raise VisualMismatch("SHAM rejects non-photographic or unverified visual style: " + reason)
        if not matched and (confidence >= 0.72 or mode == "strict"):
            raise VisualMismatch(
                f"SHAM image disagrees with joke (confidence={confidence:.2f}): {reason}"
            )
        return {
            "vision_review": ("matched" if matched else "uncertain"),
            "vision_confidence": confidence,
            "vision_reason": reason,
            "vision_photo_like": photo_like if isinstance(photo_like, bool) else None,
            "vision_model": os.getenv("SHAM_VISION_MODEL", DEFAULT_MODEL),
        }
    except VisualMismatch as exc:
        raise RuntimeError(str(exc)) from exc
    except (requests.RequestException, OSError, TypeError, KeyError, ValueError) as exc:
        if mode == "strict":
            raise RuntimeError("SHAM strict vision review unavailable: " +
                               type(exc).__name__) from exc
        return {"vision_review": "unavailable",
                "vision_reason": (type(exc).__name__ + ": " + str(exc))[:160]}
