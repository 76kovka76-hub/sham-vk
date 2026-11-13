"""Isolated one-shot DVOIQ publisher. A Telegram-like screenshot; no branding or caption."""
import os, json, time, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

BASE="https://vedismm.ru/api/v1"
GROUP="243268965"
ACCOUNT=5479
TITLE="DVOIQ — Последний дедлайн — Telegram — тест 2026-11-13"
KEY="dvoiq-one-approved-20261113-lastdeadline-v1"
OUT="dvoiq_telegram.png"

def font(sz,bold=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans-"+("Bold" if bold else "")+".ttf"
    if not bold:p="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p,sz)

def make_image(path):
    W,H=1080,1350
    img=Image.new("RGB",(W,H),"#0c1726"); d=ImageDraw.Draw(img)
    rnd=random.Random(243268965)
    for k in range(100):
        x,y=rnd.randrange(W),rnd.randrange(245,1190)
        rr=rnd.choice([8,14,20]); col="#152638"
        if k%3==0:d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=col,width=2)
        else:d.line(((x-rr,y),(x,y-rr),(x+rr,y),(x,y+rr),(x-rr,y)),fill=col,width=2)
    d.rectangle((0,0,W,231),fill="#1a2636")
    d.text((48,30),"18:47",font=font(34,True),fill="white")
    d.text((851,35),"LTE",font=font(25),fill="#eef1f5")
    for k in range(4):d.rectangle((790+k*15,76-k*10,800+k*15,88),fill="#eef1f5")
    d.rounded_rectangle((953,35,1037,72),radius=9,outline="white",width=3)
    d.rounded_rectangle((960,42,1014,65),radius=3,fill="#eef1f5")
    d.line([(69,149),(42,175),(69,200)],fill="#f7f9fc",width=7)
    d.line([(43,175),(102,175)],fill="#f7f9fc",width=7)
    d.ellipse((125,119,229,223),fill="#4a5e87")
    d.ellipse((165,141,190,169),fill="#101a2b")
    d.ellipse((146,168,211,214),fill="#101a2b")
    d.text((253,120),"Друг",font=font(43,True),fill="white")
    d.text((253,173),"в сети",font=font(27),fill="#65a8f7")
    d.arc((951,146,1002,200),20,125,fill="#f7f9fc",width=8)
    for y in (151,171,191):d.ellipse((1034,y-6,1045,y+5),fill="white")
    d.rounded_rectangle((442,272,639,327),radius=27,fill="#2a3748")
    d.text((472,278),"Сегодня",font=font(31),fill="#f8fafc")
    def bubble(lines,x,y,w,side,tm):
        hh=len(lines)*54+69
        bg="#2c3847" if side=="in" else "#3678d3"
        d.rounded_rectangle((x,y,x+w,y+hh),radius=32,fill=bg)
        if side=="in":d.polygon([(x+18,y+hh-22),(x-13,y+hh+3),(x+46,y+hh-9)],fill=bg)
        else:d.polygon([(x+w-18,y+hh-22),(x+w+13,y+hh+3),(x+w-46,y+hh-9)],fill=bg)
        for i,line in enumerate(lines):
            d.text((x+35,y+22+i*54),line,font=font(37),fill="white")
        d.text((x+w-(145 if side=="out" else 78),y+hh-37),tm,font=font(21),fill="#d4dfea")
        if side=="out":
            d.line([(x+w-42,y+hh-30),(x+w-35,y+hh-22),(x+w-21,y+hh-39)],fill="#dcecff",width=3)
            d.line([(x+w-33,y+hh-30),(x+w-26,y+hh-22),(x+w-12,y+hh-39)],fill="#dcecff",width=3)
    bubble(["Если бы тебе сообщили дату","смерти, что бы ты сделал?"],27,380,795,"in","18:41")
    bubble(["Никому на работе не сказал."],194,583,860,"out","18:44")
    bubble(["Почему?"],28,752,385,"in","18:45")
    bubble(["А то попросят закрыть задачи","заранее."],215,914,839,"out","18:46")
    d.rectangle((0,1202,W,1305),fill="#1a2636")
    d.ellipse((29,1226,86,1283),outline="#94a2b4",width=5)
    d.arc((47,1243,68,1264),0,180,fill="#94a2b4",width=4)
    d.ellipse((47,1241,52,1246),fill="#94a2b4")
    d.ellipse((64,1241,69,1246),fill="#94a2b4")
    d.text((133,1230),"Сообщение",font=font(39),fill="#7b879a")
    d.arc((906,1226,951,1281),70,340,fill="#98a6b8",width=4)
    d.ellipse((1022,1228,1047,1272),outline="#98a6b8",width=4)
    d.rounded_rectangle((1031,1219,1038,1261),radius=3,fill="#98a6b8")
    d.rounded_rectangle((423,1327,656,1335),radius=4,fill="#c0c6cd")
    img.save(path,format="PNG",optimize=True)
    assert img.size==(W,H)

def get(api,token):
    r=requests.get(BASE+api,headers={"Authorization":"Bearer "+token},timeout=35)
    if r.status_code!=200:raise RuntimeError("GET "+api+" HTTP "+str(r.status_code))
    obj=r.json()
    if "data" not in obj:raise RuntimeError("Unexpected GET response")
    return obj["data"]

def send(api,token,code,**kwargs):
    h={"Authorization":"Bearer "+token}
    h.update(kwargs.pop("headers",{}))
    r=requests.post(BASE+api,headers=h,timeout=100,**kwargs)
    if r.status_code!=code:
        raise RuntimeError("POST "+api+" HTTP "+str(r.status_code)+": "+r.text[:220])
    data=r.json().get("data")
    if not isinstance(data,dict):raise RuntimeError("Unexpected POST response")
    return data

def main():
    make_image(OUT)
    token=os.getenv("VEDISMM_TOKEN","").strip()
    if not token:raise RuntimeError("Missing GitHub Actions secret VEDISMM_TOKEN; no post attempted")
    a=get("/accounts",token)
    if not isinstance(a,list):raise RuntimeError("Accounts response was not a list")
    matches=[row for row in a if row.get("network")=="vk" and str(row.get("external_id","")).lstrip("-")==GROUP]
    if len(matches)!=1 or int(matches[0].get("id",0))!=ACCOUNT:
        raise RuntimeError("Wrong VK target: expected DVOIQ club243268965 AND account 5479; no write attempted")
    print("DVOIQ account verified: 5479 / club243268965",flush=True)
    # A stable idempotency key also protects against a repeated GitHub workflow run.
    with open(OUT,"rb") as fh:
        m=send("/media",token,201,files={"file":("dvoiq_telegram.png",fh,"image/png")})
    mid=int(m.get("id") or 0)
    if mid<=0 or m.get("type")!="image" or m.get("status")!="ready":
        raise RuntimeError("Uploaded image is not ready; no post created")
    draft=send("/posts",token,201,headers={"Idempotency-Key":KEY},json={"title":TITLE,"content":"","account_ids":[ACCOUNT],"media_ids":[mid]})
    pid=int(draft.get("id") or 0)
    version=int(draft.get("version") or 0)
    if pid<=0 or version<=0 or draft.get("status")!="draft" or not draft.get("media"):
        raise RuntimeError("Draft lacks media/status/version; publish cancelled")
    print(json.dumps({"event":"draft_created","post_id":pid,"account_id":ACCOUNT},ensure_ascii=False),flush=True)
    job=send("/posts/"+str(pid)+"/publish",token,202,headers={"Idempotency-Key":KEY+"-pub"},json={"version":version})
    jid=job.get("id")
    if not isinstance(jid,str) or not jid:raise RuntimeError("Publish accepted without job id")
    print(json.dumps({"event":"job_accepted","post_id":pid,"job_id":jid}),flush=True)
    for _ in range(24):
        time.sleep(5)
        j=get("/jobs/"+jid,token)
        state=j.get("status")
        if state in ("succeeded","partially_succeeded"):
            t=[v for v in j.get("targets",[]) if (v.get("account") or {}).get("id")==ACCOUNT and v.get("status")=="succeeded" and v.get("external_url")]
            if not t:raise RuntimeError("Job completed but DVOIQ VK URL not confirmed")
            result={"status":"published","vk_url":t[0]["external_url"],"post_id":pid,"job_id":jid}
            Path("dvoiq_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
            print(json.dumps(result,ensure_ascii=False),flush=True)
            return
        if state in ("failed","cancelled"):raise RuntimeError("VediSMM job failed: "+str(j.get("error_code") or state))
    result={"status":"awaiting_confirmation","post_id":pid,"job_id":jid}
    Path("dvoiq_result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result),flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("DVOIQ publication failed safely:",str(e),flush=True)
        sys.exit(1)
