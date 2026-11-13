"""Anonymous-free visual quality gate for every new synthetic SOVETSKIY meme.

Requires actual image understanding, not merely similarity of the TEXT prompt.
Uses the previously verified OVHcloud anonymous multimodal Mistral endpoint.
No paid key, no false guarantee: VLM judgments can still be mistaken.

When unavailable or uncertain: FAIL CLOSED, not a random photo fallback.
"""
import base64
import json
from pathlib import Path
import random
import threading
import time

import requests

MODEL="Mistral-Small-3.2-24B-Instruct-2506"
API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
MIN_SPACING_SECONDS=37
_lock=threading.Lock()
_next_request_at=0.0


def _rate_limit():
    global _next_request_at
    with _lock:
        delay=_next_request_at-time.monotonic()
        if delay>0:
            time.sleep(delay)
        _next_request_at=time.monotonic()+MIN_SPACING_SECONDS


def inspect(path,top,bottom,visual_intent,post=requests.post):
    if not all(isinstance(x,str) and x.strip() for x in (top,bottom,visual_intent)):
        raise RuntimeError("Cannot evaluate empty visual-joke pairing")
    binary=Path(path).read_bytes()
    if not 20_000<=len(binary)<=14_000_000:
        raise RuntimeError("Image for visual review is missing or too large")
    encoded=base64.b64encode(binary).decode("ascii")
    ask=(
        "You are a strict independent VISUAL QA reviewer for a humor "
        "post with an AI generated photograph. DO NOT agree just because "
        "the author describes the wanted image. LOOK at actual image content. "
        "First identify visible people, props, expressions and physical actions. "
        "The published joke (in Russian) is: TOP: "+top+" BOTTOM: "+bottom+". "
        "The expected concrete real-world scene is: "+visual_intent+". "
        "Check whether the important prop and key action are visibly "
        "present and consistent with the joke, without assuming hidden context. "
        "Also check whether large Cyrillic headline/caption appears legible. "
        "For a joke about a giant receipt, an image with no receipt MUST FAIL. "
        "For a joke about a pillow holding someone in bed, a man struggling "
        "with a big pillow MAY PASS. If doubtful, FAIL. "
        "Output ONLY JSON with keys: visual_description (min 30 English chars), "
        "central_prop_visible (boolean), action_matches_joke (boolean), "
        "large_caption_legible (boolean), explanation (min 45 English chars)."
    )
    payload={
        "model":MODEL,
        "messages":[{"role":"user","content":[
            {"type":"text","text":ask},
            {"type":"image_url","image_url":{
                "url":"data:image/png;base64,"+encoded
            }}
        ]}],
        "temperature":0.0,"max_tokens":690,"stream":False
    }
    for attempt in range(3):
        _rate_limit()
        response=post(API,json=payload,
            headers={"Content-Type":"application/json","Accept":"application/json"},
            timeout=125)
        if response.status_code==429:
            try:
                delay=int(response.headers.get("Retry-After") or 45)
            except (TypeError,ValueError):
                delay=45
            if attempt>=2 or delay>120:
                raise RuntimeError("Free vision model is rate-limited, failing closed")
            time.sleep(max(delay,45))
            continue
        if response.status_code in (401,402,403):
            raise RuntimeError("Free vision model unavailable HTTP "+str(response.status_code))
        response.raise_for_status()
        break
    else:
        raise RuntimeError("Free visual review unavailable")

    payload=response.json()
    candidates=payload.get("choices") or []
    if not candidates:
        raise RuntimeError("Vision answer is empty")
    raw=(candidates[0].get("message") or {}).get("content")
    if not isinstance(raw,str) or len(raw)>8000:
        raise RuntimeError("Vision evaluator returned invalid text")
    first,last=raw.find("{"),raw.rfind("}")
    if first<0 or last<=first:
        raise RuntimeError("Vision evaluator did not return a JSON object")
    data=json.loads(raw[first:last+1])
    if not isinstance(data,dict):
        raise RuntimeError("Vision evaluation must be a JSON object")
    for field in ("central_prop_visible","action_matches_joke","large_caption_legible"):
        if type(data.get(field)) is not bool:
            raise RuntimeError("Vision evaluation missing strict boolean "+field)
    for field,minimum in (("visual_description",30),("explanation",45)):
        if not isinstance(data.get(field),str) or len(data[field].strip())<minimum:
            raise RuntimeError("Uninformative visual evaluation: "+field)
    approved=all(data[x] for x in
        ("central_prop_visible","action_matches_joke","large_caption_legible"))
    result={"passed":approved,"description":data["visual_description"][:440],
            "explanation":data["explanation"][:520],
            "central_prop_visible":data["central_prop_visible"],
            "action_matches_joke":data["action_matches_joke"],
            "large_caption_legible":data["large_caption_legible"],
            "model":MODEL,"source":"anonymous_free_vision"}
    print("SOVETSKIY_VISUAL_REVIEW:",json.dumps(result,ensure_ascii=False),flush=True)
    return result
