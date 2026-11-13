"""Best-effort multimodal scene-vs-image review for SHAM.

Uses the same existing free OVH endpoints, no TinyFish or secret.
Requests can be throttled/unavailable on the anonymous tier. In best_effort
mode a confident mismatch blocks publication; an unavailable model is marked
as unverified, never misreported as approved. Strict mode fails closed.
"""
import base64
import io
import json
import os

import requests

URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/responses"
DEFAULT_MODEL = "Qwen3.5-9B"


def _extract_text(response):
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    for block in response.get("output", []):
        if not isinstance(block, dict):
            continue
        for part in block.get("content", []):
            if isinstance(part, dict) and part.get("type") == "output_text":
                return part.get("text") or ""
    return ""


def _json_object(text):
    if not isinstance(text, str) or len(text) > 12000:
        raise ValueError("Invalid vision response")
    index = text.find("{")
    if index < 0:
        raise ValueError("Vision response had no JSON")
    obj, _ = json.JSONDecoder().raw_decode(text[index:])
    if not isinstance(obj, dict):
        raise ValueError("Bad vision JSON")
    return obj


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
        preview.save(buf, "JPEG", quality=75, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        scene = str(post.get("visual", ""))[:500]
        joke = (str(post.get("top", "")) + "\n" + str(post.get("bottom", "")))[:400]
        instructions = (
            "You are an independent visual QA editor for a Russian comedy meme. "
            "Study the actual attached image (not an imagined one). "
            "Russian joke: " + joke +
            "\nIntended physical scene: " + scene +
            "\nDoes this ACTUAL image show the main characters, important objects "
            "and physical action from the joke's punchline? A generic portrait "
            "or unrelated pretty background is a mismatch. Ignore the lack of "
            "text overlay. Return ONLY compact JSON with keys "
            "matches (boolean), confidence (number 0..1), reason (short English)."
        )
        token = os.getenv("SHAM_VISION_API_KEY", "").strip()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        reply = request(
            URL,
            headers=headers,
            json={
                "model": os.getenv("SHAM_VISION_MODEL", DEFAULT_MODEL),
                "store": False,
                "max_output_tokens": 200,
                "input": [{
                    "type": "message", "role": "user",
                    "content": [
                        {"type": "input_text", "text": instructions},
                        {"type": "input_image",
                         "image_url": "data:image/jpeg;base64," + b64},
                    ],
                }],
            },
            timeout=22,
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
        if not matched and (confidence >= 0.78 or mode == "strict"):
            raise ValueError(f"SHAM image disagrees with joke (vision confidence={confidence:.2f}): {reason}")
        return {
            "vision_review": ("matched" if matched else "uncertain"),
            "vision_confidence": confidence,
            "vision_reason": reason,
        }
    except (requests.RequestException, OSError, TypeError, KeyError, ValueError) as exc:
        # The model can be unavailable on the free lane: be transparent.
        # A confident mismatch is NOT an availability failure.
        if "SHAM image disagrees with joke" in str(exc) or mode == "strict":
            raise RuntimeError(str(exc)) from exc
        return {"vision_review": "unavailable",
                "vision_reason": (type(exc).__name__ + ": " + str(exc))[:160]}
