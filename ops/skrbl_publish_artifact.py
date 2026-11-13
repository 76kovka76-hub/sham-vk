"""Publish an EXPLICITLY reviewed free-Horde SKRBL preview artifact.

Never generate or modify artwork; use the exact image hash the editorial
reviewer confirmed. Strict target group 243241856 and idempotent post key.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"skrbl"))
from publish_test import BASE,_data,_target_account,_valid_vk_url

ART=ROOT/"reviewed_artifact"
IMAGE=ART/"free_comic_trial.png"
META=ART/"free_comic_trial.json"

def main():
    if os.getenv("SKRBL_SEND_APPROVED")!="true":
        raise RuntimeError("SKRBL_SEND_APPROVED gate is not open")
    expected=os.getenv("SKRBL_APPROVED_SHA256","").strip()
    if len(expected)!=64 or not all(ch in "0123456789abcdef" for ch in expected):
        raise RuntimeError("Explicit editorial-approved image SHA256 required")
    if not IMAGE.is_file() or not META.is_file():
        raise RuntimeError("Approved artifact missing")
    actual=hashlib.sha256(IMAGE.read_bytes()).hexdigest()
    if actual!=expected:
        raise RuntimeError("Approved comic checksum mismatch; no VK post")
    metadata=json.loads(META.read_text(encoding="utf-8"))
    if metadata.get("sha256")!=actual or metadata.get("panels")!=4 or metadata.get("generated_by")!="AI Horde volunteer network":
        raise RuntimeError("Not an approved free 4-panel comic artifact")
    token=os.getenv("VEDISMM_TOKEN","").strip()
    if not token:
        raise RuntimeError("Missing VEDISMM_TOKEN")
    headers={"Authorization":"Bearer "+token}
    account=_target_account(headers)
    print("SKRBL_TARGET_ACCOUNT:",account)
    with IMAGE.open("rb") as fh:
        upload=requests.post(BASE+"/media",headers=headers,
            files={"file":("SKRBL_free_comic_approved.png",fh,"image/png")},timeout=95)
    media=_data(upload,201)
    if media.get("type")!="image" or media.get("status")!="ready":
        raise RuntimeError("Image is not ready; aborted")
    idm="skrbl-approved-free-comic-"+actual[:35]
    content=("Решил быстренько проверить рабочую почту.\n"
             "347 писем, каждое «срочно». Кажется, теперь письма реально пытаются меня сожрать.\n"
             "Бл***ь, и зачем я проснулся?\n\n"
             "#SKRBL #юмор #карандашныемемы")
    draft=requests.post(BASE+"/posts",
        headers={**headers,"Idempotency-Key":idm},
        json={"title":"SKRBL — бесплатный карандашный комикс (проверка)",
              "content":content,"account_ids":[account],"media_ids":[int(media["id"])]},timeout=45)
    p=_data(draft,201)
    post_id,version=int(p.get("id") or 0),int(p.get("version") or 0)
    if not post_id or not version or p.get("status")!="draft" or not p.get("media"):
        raise RuntimeError("Bad VediSMM draft; aborted")
    jobresp=requests.post(BASE+f"/posts/{post_id}/publish",
        headers={**headers,"Idempotency-Key":idm+"-publish"},
        json={"version":version},timeout=45)
    job=_data(jobresp,202)
    jid=job.get("id")
    if not isinstance(jid,str) or not jid:
        raise RuntimeError("Missing publish job")
    print("SKRBL_NEW_POST_ID:",post_id)
    for _ in range(24):
        time.sleep(5)
        result=_data(requests.get(BASE+f"/jobs/{jid}",headers=headers,timeout=35),200)
        if result.get("status") in ("succeeded","partially_succeeded"):
            urls=[t["external_url"] for t in result.get("targets",[])
                  if t.get("account",{}).get("id")==account
                  and t.get("status")=="succeeded"
                  and _valid_vk_url(t.get("external_url"))]
            if not urls:raise RuntimeError("VK SKRBL publication not verified")
            print("SKRBL_REVIEWED_FREE_POST_URL:",urls[0])
            return
        if result.get("status") in ("failed","cancelled"):
            raise RuntimeError("VediSMM publication failed")
    raise RuntimeError("VediSMM accepted job but VK delivery not confirmed")

if __name__=="__main__":
    main()
