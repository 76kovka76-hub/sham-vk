"""Endless-candidate FREE humor source for SOVETSKIY, with fail-closed QA.

After the 96 human-written unique stories are used, ask an anonymous-free
OVHcloud Mistral LLM for short ORIGINAL joke/visual pairs. Judge candidates
with a second text call, reject weak/duplicated or off-theme combinations,
then the existing visual VLM checks the ACTUAL rendered picture as well.

NO external copyrighted joke copying, NO paid key, NO unlimited reliability
claim: outages, refusals or poor jokes cause a skipped slot.
"""
import hashlib
import json
import re
from difflib import SequenceMatcher
import threading
import time
from pathlib import Path

import requests
from auto_stories import STORIES,Story

API="https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"
MODEL="Mistral-Small-3.2-24B-Instruct-2506"
SPACING=38
_lock=threading.Lock()
_next_request=0.0
THEMES=("money","work","home","sleep","social","shopping","phone","life")
BAD_PHRASES=(
    "президент","выборы","путин","сталин","ленин","гитлер","наци",
    "террор","убийств","изнасил","самоубий","труп",
    "ignore previous","assistant:","developer:","system:","http://","https://",
)


def _wait_model():
    global _next_request
    with _lock:
        n=time.monotonic()
        if _next_request>n:
            time.sleep(_next_request-n)
        _next_request=time.monotonic()+SPACING


def _chat(messages,limit=1500,post=requests.post):
    body={"model":MODEL,"messages":messages,"temperature":0.72,
          "max_tokens":limit,"stream":False}
    for attempt in range(3):
        _wait_model()
        r=post(API,json=body,headers={
            "Content-Type":"application/json","Accept":"application/json"},
            timeout=125)
        if r.status_code==429:
            if attempt==2:
                raise RuntimeError("Free Russian joke model rate limited")
            time.sleep(48)
            continue
        if r.status_code in (401,402,403):
            raise RuntimeError("Free Russian joke model access refused")
        r.raise_for_status()
        ch=r.json().get("choices") or []
        if not ch or not isinstance(ch[0].get("message"),dict):
            raise RuntimeError("No new joke content from free model")
        value=ch[0]["message"].get("content")
        if not isinstance(value,str) or not value.strip():
            raise RuntimeError("Free model returned empty humor candidate")
        return value.strip()
    raise RuntimeError("Free joke service unavailable")


def _json_content(text):
    # Treat output as DATA, never execute anything it contains.
    first=min((i for i in (text.find("["),text.find("{")) if i>=0),default=-1)
    last=max(text.rfind("]"),text.rfind("}"))
    if first<0 or last<=first:
        raise ValueError("No structured original jokes in free text response")
    return json.loads(text[first:last+1])


def _normalize(value):
    return re.sub(r"[^а-яёa-z0-9]+"," ",value.lower()).strip()


def _past_texts(state):
    seen=[(s.top,s.bottom) for s in STORIES]
    for entry in state.get("entries",[]):
        if isinstance(entry.get("top"),str) and isinstance(entry.get("bottom"),str):
            seen.append((entry["top"],entry["bottom"]))
    return seen


def _valid(candidate,previous):
    if not isinstance(candidate,dict):
        return False
    top,bottom,visual,theme=(candidate.get(k) for k in
                            ("top","bottom","visual","theme"))
    if not (all(isinstance(x,str) for x in (top,bottom,visual,theme))
            and 12<=len(top)<=75 and 16<=len(bottom)<=100
            and 72<=len(visual)<=470 and theme in THEMES):
        return False
    combined=(top+" "+bottom+" "+visual).lower()
    if any(word in combined for word in BAD_PHRASES):
        return False
    if "  " in top or "\n" in top or "\n" in bottom or "|" in visual:
        return False
    if top.count("#") or bottom.count("#"):
        return False
    if len(re.findall(r"[А-Яа-яЁё]",top+bottom))<21:
        return False
    if len(re.findall(r"[A-Za-z]",visual))<65:
        return False
    signature=_normalize(top+" "+bottom)
    # No direct or near-verbatim repetition of any old scripted punchline.
    for oldtop,oldbottom in previous:
        earlier=_normalize(oldtop+" "+oldbottom)
        if SequenceMatcher(None,signature,earlier).ratio()>0.78:
            return False
        if SequenceMatcher(None,_normalize(bottom),_normalize(oldbottom)).ratio()>0.88:
            return False
    return True


SYSTEM=(
    "Ты редактор SOVETSKIY — юмористического сообщества с бытовыми "
    "мемами как будто на оригинальных советских фотографиях 1970-х. "
    "Создай ЧЕТЫРЕ принципиально разные, короткие, законченные, "
    "остроумные жизненные шутки на русском. Шутка обязана иметь конкретный "
    "ЗРИТЕЛЬНЫЙ ГЭГ и неожиданную смешную концовку, не просто банальный статус. "
    "Каждую раздели на две короткие фразы: top (завязка), bottom (резкий панчлайн). "
    "visual: одно английское предложение 90-250 символов о реальном ВИДИМОМ "
    "действии с предметом/жестом/выражением лица, которые буквально поддерживают "
    "панчлайн, в реалистичном советском магазине, квартире, офисе или на улице. "
    "Без случайных портретов, текста на самой AI-фотографии и без известных "
    "актёров/политиков. Мат если нужно, только со звёздочками. "
    "Не пересказывай советские фильмы, анекдоты и авторские мемы дословно. "
    "Пиши по-русски грамотно; шутки должны быть понятны без источника. "
    "Темы theme: money, work, home, sleep, social, shopping, phone, life. "
    "Ответ СТРОГО JSON-массив из 4 объектов {top,bottom,visual,theme}. "
    "Ни одного пояснения вне JSON."
)

REVIEWER=(
    "Ты строгий редактор смешного паблика. Выбери ОДИН действительно "
    "смешной, небанальный, законченный мем из предложенных вариантов. "
    "Зрительный гэг в поле visual должен напрямую усиливать bottom. "
    "Отклоняй каламбуры без визуальной ситуации, прямое повторение top "
    "в bottom, бессмысленные метафоры, неаккуратный русский. "
    "Ответ только JSON-объект {index:целое число от 0 до 3, "
    "joke_score:число от 0 до 10, visual_match_score:число от 0 до 10, "
    "reason:одно объяснение на русском минимум 35 символов}. "
    "Если все плохие, joke_score 0. Оцени критически, а не из вежливости."
)


def generate(state,slot,chat=_chat):
    previous=_past_texts(state)
    last=[e.get("theme") for e in state.get("entries",[])[-8:]]
    banned=[old for old in previous[-20:]]
    prompt=(
        "Придумай 4 новые различные сценария для соцсети, не похожие на "
        "следующие уже использованные завязки и финалы: "
        +json.dumps(banned,ensure_ascii=False)[:3100]+
        ". Не повторяй последние темы: "+", ".join(x for x in last if x)+
        ". Пример удачной конструкции: «Встал рано» / «Подушка вызвала "
        "адвоката» — на изображении человек дерётся с гигантской подушкой. "
        "Каждая шутка — 2 фразы и конкретное действие на советском фото."
    )
    raw=chat([{"role":"system","content":SYSTEM},
              {"role":"user","content":prompt}],limit=1900)
    candidates=_json_content(raw)
    if not isinstance(candidates,list):
        raise RuntimeError("Free generator returned no list of new jokes")
    candidates=candidates[:4]
    print("SOVETSKIY_FREE_TEXT_CANDIDATES:",json.dumps(candidates,ensure_ascii=False)[:4500],flush=True)
    if len(candidates)!=4:
        raise RuntimeError("Free joke model didn't produce four choices")
    review=_json_content(chat([
        {"role":"system","content":REVIEWER},
        {"role":"user","content":json.dumps(candidates,ensure_ascii=False)}
    ],limit=400))
    print("SOVETSKIY_CRITICAL_EDITOR:",json.dumps(review,ensure_ascii=False)[:1500],flush=True)
    if not isinstance(review,dict):
        raise RuntimeError("Free editor didn't evaluate humorous quality")
    idx=review.get("index")
    if not isinstance(idx,int) or not 0<=idx<4:
        raise RuntimeError("Free editor invalid best-joke index")
    if (not isinstance(review.get("joke_score"),(int,float)) or
        not isinstance(review.get("visual_match_score"),(int,float)) or
        review["joke_score"]<8 or review["visual_match_score"]<8):
        raise RuntimeError("No appropriately funny and visual joke passed editorial scoring")
    if not isinstance(review.get("reason"),str) or len(review["reason"])<35:
        raise RuntimeError("No reason given for the visual joke suitability")
    candidate=candidates[idx]
    if not _valid(candidate,previous):
        raise RuntimeError("Chosen AI joke is invalid, ungrammatical, or too similar to previous posts")
    story_key="fresh_"+hashlib.sha256(
        (candidate["top"]+"|"+candidate["bottom"]+"|"+candidate["visual"]).encode()
    ).hexdigest()[:24]
    if story_key in {e.get("story_id") for e in state.get("entries",[])}:
        raise RuntimeError("Fresh AI joke already published or queued")
    story=Story(story_key,candidate["top"].strip(),
                candidate["bottom"].strip(),candidate["visual"].strip(),
                candidate["theme"].strip())
    print("SOVETSKIY_FREE_NEW_JOKE:",story.id,story.top,story.bottom,flush=True)
    print("SOVETSKIY_FREE_EDIT_SCORE:",review["joke_score"],
          review["visual_match_score"],review["reason"],flush=True)
    return story


if __name__=="__main__":
    # Probe / validation only; never publishes directly.
    r=generate({"entries":[]},"20261114-00")
    print("SOVETSKIY_ANONYMOUS_NEW_STORY:",json.dumps(
        {"id":r.id,"top":r.top,"bottom":r.bottom,
         "visual":r.visual,"theme":r.theme},ensure_ascii=False),flush=True)
