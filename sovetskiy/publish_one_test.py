"""Publish exactly the visually-reviewed SOVETSKIY meme to VK group 243244760.

The previously generated real photo is downloaded from a PINNED GitHub
Actions artifact; its hash must match the reviewed image. The old punchline
about a receipt was rejected during visual review because the model drew NO
receipt; this script changes only that text to match the visible man selecting
bread. No unrelated photo and no changes to SHAM/SKRBL.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
import requests
from check_account import BASE, VK_GROUP_ID, find_account

ROOT=Path(__file__).resolve().parent
ART=ROOT/"reviewed_gastronom"
SOURCE=ART/"test_gastronom.png"
META=ART/"test_gastronom.json"
OUTPUT=ROOT/"sovetskiy_gastronom_published.png"
RESULT=ROOT/"sovetskiy_test_publish_result.json"

SOURCE_SHA256="3d05869eaf64fb1c96a06398a2dd646a69e204bf96f276a098a56cd0c727d8e3"
SOURCE_RUN_ID="43408214337"
ONE_OFF_KEY="sovetskiy-gastronom-bread-choice-20261113-v1"
BOTTOM="ВЫБИРАЮ УЖЕ ТРЕТЬЮ ПЯТИЛЕТКУ."
CAPTION=(
    "Пока выбирал батон, в гастрономе успели смениться три пятилетки "
    "и два директора.\n\n#SOVETSKIY #юмор #жиза"
)

def _data(r, expected):
    r.raise_for_status()
    if r.status_code!=expected:
        raise RuntimeError(f"VediSMM unexpected HTTP {r.status_code}, expected {expected}")
    obj=r.json()
    if not isinstance(obj,dict) or not isinstance(obj.get("data"),dict):
        raise RuntimeError("VediSMM invalid response")
    return obj["data"]


def _valid_vk_url(url):
    if not isinstance(url,str):return False
    u=urlparse(url)
    return (u.scheme=="https" and u.hostname in
            ("vk.com","vk.ru","www.vk.com","www.vk.ru") and
            re.fullmatch(r"/wall-243244760_\d+",u.path) is not None)


def prepare_reviewed_image():
    if not SOURCE.is_file() or not META.is_file():
        raise RuntimeError("Pinned, reviewed GitHub image artifact missing")
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest!=SOURCE_SHA256:
        raise RuntimeError("Source SHA256 differs from the image visually reviewed by editor")
    data=json.loads(META.read_text(encoding="utf-8"))
    if (data.get("image_sha256")!=SOURCE_SHA256 or
        data.get("group_id")!=VK_GROUP_ID or
        data.get("real_film_still") is not False or
        data.get("size")!=[1200,1200]):
        raise RuntimeError("Source metadata or group does not match")
    with Image.open(SOURCE) as original:
        img=original.convert("RGB")
    if img.size!=(1200,1200):raise RuntimeError("Unexpected preview size")
    d=ImageDraw.Draw(img)
    d.rectangle((0,1043,1199,1160),fill=(240,222,187))
    fontpath="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
    for fontsize in range(53,25,-1):
        f=ImageFont.truetype(fontpath,fontsize)
        if d.textbbox((0,0),BOTTOM,font=f)[2]<1110:break
    else:
        raise RuntimeError("Corrected text does not fit the mobile meme layout")
    d.text((600,1080),BOTTOM,font=f,fill=(30,28,25),anchor="mt")
    img.save(OUTPUT,format="PNG",optimize=True)
    sha=hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print("SOVETSKIY_REVIEWED_PHOTO_SHA256:",SOURCE_SHA256,flush=True)
    print("SOVETSKIY_PUBLISH_IMAGE_SHA256:",sha,flush=True)
    print("SOVETSKIY_REVIEWED_JOKE:",BOTTOM,flush=True)
    return OUTPUT


def publish():
    if os.getenv("SOVETSKIY_ONE_OFF_APPROVED")!="true":
        raise RuntimeError("Explicit one-off approval gate missing")
    path=prepare_reviewed_image()
    token=os.getenv("VEDISMM_TOKEN","").strip()
    account=find_account(token)
    headers={"Authorization":"Bearer "+token}
    print("SOVETSKIY_STRICT_TARGET:",VK_GROUP_ID,account,flush=True)
    with path.open("rb") as src:
        u=requests.post(BASE+"/media",headers=headers,
                        files={"file":("SOVETSKIY_bread_choice.png",src,"image/png")},
                        timeout=110)
    media=_data(u,201)
    mid=int(media.get("id") or 0)
    if mid<=0 or media.get("status")!="ready" or media.get("type")!="image":
        raise RuntimeError("VediSMM did not confirm image upload")
    created=requests.post(BASE+"/posts",
        headers={**headers,"Idempotency-Key":ONE_OFF_KEY},
        json={"title":"SOVETSKIY — выбирал батон третью пятилетку",
              "content":CAPTION,"account_ids":[account],
              "media_ids":[mid]},timeout=50)
    draft=_data(created,201)
    pid,version=int(draft.get("id") or 0),int(draft.get("version") or 0)
    if not pid or not version or draft.get("status")!="draft" or not draft.get("media"):
        raise RuntimeError("VediSMM did not confirm draft with image")
    pub=requests.post(BASE+f"/posts/{pid}/publish",
        headers={**headers,"Idempotency-Key":ONE_OFF_KEY+"-publish"},
        json={"version":version},timeout=50)
    job=_data(pub,202)
    jid=job.get("id")
    if not isinstance(jid,str) or not jid:
        raise RuntimeError("VediSMM returned no publication job id")
    print("SOVETSKIY_VEDISMM_POST_ID:",pid,flush=True)
    for _ in range(25):
        time.sleep(5)
        status=_data(requests.get(BASE+f"/jobs/{jid}",headers=headers,timeout=35),200)
        if status.get("status") in ("succeeded","partially_succeeded"):
            targets=[t for t in status.get("targets",[])
                     if t.get("account",{}).get("id")==account
                     and t.get("status")=="succeeded"
                     and _valid_vk_url(t.get("external_url"))]
            if not targets:
                raise RuntimeError("VediSMM did not confirm VK delivery to target group")
            url=targets[0]["external_url"]
            RESULT.write_text(json.dumps({
                "url":url,"group_id":VK_GROUP_ID,"post_id":pid,
                "joke":BOTTOM,"image_sha256":hashlib.sha256(path.read_bytes()).hexdigest()
            },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print("SOVETSKIY_PUBLISHED_URL:",url,flush=True)
            return url
        if status.get("status") in ("failed","cancelled"):
            raise RuntimeError("VediSMM job failed: "+str(status.get("status")))
    raise RuntimeError("VediSMM job accepted but VK delivery not confirmed")


if __name__=="__main__":
    publish()
