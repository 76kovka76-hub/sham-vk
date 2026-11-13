"""Verify anonymous-free multimodal judgment of real SKRBL/SOVETSKIY memes.

Probe ONLY; no publication. A language model must not be treated as infallible
proof that the image matches the joke. Fail closed on vague or invalid answers.
"""
import base64
import json
from pathlib import Path
import re

import requests

ROOT=Path(__file__).resolve().parent
IMAGE=ROOT/"vision_review"/"auto15_preview.png"
RESULT=ROOT/"vision_review_result.json"
MODEL="Mistral-Small-3.2-24B-Instruct-2506"
API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"

EXPECTED_TOP="ПЫТАЛСЯ ВСТАТЬ ПОРАНЬШЕ."
EXPECTED_BOTTOM="ПОДУШКА ПОДАЛА АПЕЛЛЯЦИЮ."
EXPECTED_SCENE="A Soviet man being physically detained in bed by a gigantic fluffy pillow."


def check(image=IMAGE,post=requests.post):
    binary=Path(image).read_bytes()
    if not 10_000<len(binary)<12_000_000:
        raise RuntimeError("Invalid reviewed image size")
    b64=base64.b64encode(binary).decode()
    task=(
        "Evaluate a Russian-language humor meme picture and its joke. "
        "First look at the ACTUAL VISIBLE image, not what should be there. "
        "Is the physical action and central prop clearly consistent with "
        "the short caption? This is NOT a question about artistic quality. "
        "Expected visual idea: "+EXPECTED_SCENE+" "
        "Top text: "+EXPECTED_TOP+" Bottom text: "+EXPECTED_BOTTOM+" "
        "Respond ONLY with one JSON object: "
        "{\"visual_description\":\"describe concrete objects you can see\","
        "\"central_prop_visible\":true or false,"
        "\"action_matches_joke\":true or false,"
        "\"explanation\":\"explain the visible action and reason for verdict\"}. "
        "Be skeptical; if the caption references an object not actually visible, "
        "return false. Do NOT invent items. "
    )
    res=post(API,
         json={"model":MODEL,"messages":[{"role":"user","content":[
             {"type":"text","text":task},
             {"type":"image_url","image_url":{"url":"data:image/png;base64,"+b64}}
         ]}],"max_tokens":800,"temperature":0.0,"stream":False},
         headers={"Content-Type":"application/json","Accept":"application/json"},
         timeout=120)
    if res.status_code in (401,402,403,429):
        raise RuntimeError("Free vision evaluator unavailable HTTP "+str(res.status_code))
    res.raise_for_status()
    choices=res.json().get("choices") or []
    if not choices:
        raise RuntimeError("Vision evaluator returned no candidates")
    msg=choices[0].get("message") or {}
    raw=msg.get("content")
    if not isinstance(raw,str):
        raise RuntimeError("Vision evaluator result is not text")
    print("SOVETSKIY_FREE_VISION_RAW:",repr(raw[:1300]),flush=True)
    i=raw.find("{")
    j=raw.rfind("}")
    if i<0 or j<=i:
        raise RuntimeError("Vision answer is not parseable JSON")
    parsed=json.loads(raw[i:j+1])
    if not isinstance(parsed,dict):
        raise RuntimeError("Vision check must return an object")
    if not isinstance(parsed.get("visual_description"),str) or len(parsed["visual_description"])<25:
        raise RuntimeError("Uninformative vision output")
    if type(parsed.get("central_prop_visible")) is not bool or type(parsed.get("action_matches_joke")) is not bool:
        raise RuntimeError("Vision verdict is ambiguous")
    if not isinstance(parsed.get("explanation"),str) or len(parsed["explanation"])<25:
        raise RuntimeError("Vision verdict lacks image-grounded explanation")
    RESULT.write_text(json.dumps(parsed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOVETSKIY_FREE_VISION_VERDICT:",json.dumps(parsed,ensure_ascii=False),flush=True)
    return parsed


if __name__=="__main__":
    check()
