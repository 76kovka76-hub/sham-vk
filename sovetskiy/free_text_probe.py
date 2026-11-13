"""Probe genuinely free anonymous OVHcloud chat for fresh original SOVETSKIY jokes.

Does NOT publish anything. Never assume the model is free merely because a
paid API key exists; all calls are anonymous and use no billing account.
"""
import json
import os
import re
from pathlib import Path

import requests

API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
MODEL="Mistral-Small-3.2-24B-Instruct-2506"
ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/"free_text_probe.json"

SYSTEM=(
    "Ты редактор российского юмористического паблика SOVETSKIY. "
    "Пиши новые, очень короткие, злободневные, действительно смешные мемы "
    "с современной бытовой шуткой и оригинальной фотореалистичной сценой СССР 1970-х. "
    "Ответь СТРОГО JSON массивом без markdown: 3 объекта, ключи "
    "top, bottom, visual, theme. top и bottom — на грамотном русском, "
    "не больше 65 символов каждый, visual — на английском 80-220 символов "
    "и описывает ВИДИМОЕ ДЕЙСТВИЕ и конкретный предмет, который помогает шутке. "
    "Смешной поворот должен быть зрительным, а не абстрактным афоризмом. "
    "Темы: бытовуха, зарплата, магазин, работа, сон, соседи, родня. "
    "Без политики, знаменитостей, товарных знаков, копирования чужих анекдотов, "
    "без жестокости, без эротики. Мат если нужен — только со звёздочками."
)


def probe(post=requests.post):
    request={"model":MODEL,"messages":[{"role":"system","content":SYSTEM},
        {"role":"user","content":"Придумай три не похожие друг на друга оригинальные шутки: 1 про магазин, 2 про работу, 3 про квартиру. Возвращай JSON."}],
        "temperature":0.75,"max_tokens":1800,"stream":False}
    response=post(API,json=request,
        headers={"Content-Type":"application/json","accept":"application/json"},
        timeout=110)
    if response.status_code in (401,402,403,429):
        raise RuntimeError("OVH anonymous chat not available: HTTP "+str(response.status_code))
    response.raise_for_status()
    data=response.json()
    choices=data.get("choices") or []
    if not choices or not isinstance(choices[0].get("message"),dict):
        raise RuntimeError("Free text model did not return a message")
    result=choices[0]["message"].get("content")
    if isinstance(result,list):
        result="\n".join(str(x.get("text","")) for x in result if isinstance(x,dict))
    if not isinstance(result,str) or len(result)>9000:
        raise RuntimeError("Invalid generated meme text")
    cleaned=result.strip()
    print("SOVETSKIY_ANONYMOUS_LLM_RAW_START:",repr(cleaned[:1600]),flush=True)
    if not cleaned:
        raise RuntimeError("Free text model returned empty answer")
    # Read only the JSON array, not chatter/Markdown before or after it.
    begin=cleaned.find("[")
    end=cleaned.rfind("]")
    if begin>=0 and end>begin:
        cleaned=cleaned[begin:end+1]
    items=json.loads(cleaned)
    if not isinstance(items,list) or len(items)!=3:
        raise RuntimeError("Need exactly three newly generated jokes")
    for item in items:
        if (not isinstance(item,dict)
            or not all(isinstance(item.get(x),str) for x in ("top","bottom","visual","theme"))
            or not 8<=len(item["top"])<=90
            or not 8<=len(item["bottom"])<=100
            or not 60<=len(item["visual"])<=350):
            raise RuntimeError("Free LLM cannot satisfy meme format")
    OUTPUT.write_text(json.dumps(items,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOVETSKIY_FREE_ANONYMOUS_JOKES:",json.dumps(items,ensure_ascii=False),flush=True)
    return items


if __name__=="__main__":
    probe()
