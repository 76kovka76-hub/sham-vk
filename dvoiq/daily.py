#!/usr/bin/env python3
"""DVOIQ: native Telegram/Threads screenshots; schedule at most ten original posts per day."""
import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont

BASE="https://vedismm.ru/api/v1"
ACCOUNT=5479
GROUP="243268965"
TZ=ZoneInfo("Europe/Amsterdam")
BANK=Path(__file__).with_name("bank.json")
SLOTS=[(9,0),(10,30),(12,0),(13,30),(15,0),(16,30),(18,0),(19,30),(21,0),(22,30)]
W,H=1080,1350

def f(size,bold=False):
    path="/usr/share/fonts/truetype/dejavu/DejaVuSans"+("-Bold" if bold else "")+".ttf"
    return ImageFont.truetype(path,size)

def wrap(draw,txt,thefont,maxw):
    result=[]
    for paragraph in txt.split("\n"):
        line=""
        for word in paragraph.split():
            s=(line+" "+word).strip()
            if draw.textlength(s,font=thefont)<=maxw:line=s
            else:
                if line:result.append(line)
                line=word
                if draw.textlength(line,font=thefont)>maxw:
                    raise RuntimeError("Overlong unbreakable word in editorial content")
        if line:result.append(line)
    return result

def chat_image(item,path):
    light=int(item["id"][-2:])%4==0
    bg="#e4edf5" if light else "#0c1726"
    im=Image.new("RGB",(W,H),bg);d=ImageDraw.Draw(im)
    ink="#1d2634" if light else "#ffffff"
    top="#f7fafb" if light else "#1a2636"
    incoming="#ffffff" if light else "#2c3847"
    outgoing="#c9e8bd" if light else "#3678d3"
    rnd=random.Random(int(hashlib.sha256(item["id"].encode()).hexdigest()[:8],16))
    for _ in range(115):
        x,y=rnd.randrange(W),rnd.randrange(246,1190);r=rnd.choice([7,12,18]);col="#dce5ef" if light else "#152638"
        d.ellipse((x-r,y-r,x+r,y+r),outline=col,width=2)
    d.rectangle((0,0,W,225),fill=top)
    d.text((53,30),"18:47",font=f(35,True),fill=ink)
    d.text((843,35),"LTE",font=f(26),fill=ink)
    d.rounded_rectangle((962,35,1040,74),radius=8,outline=ink,width=3)
    d.rounded_rectangle((968,42,1020,66),radius=4,fill=ink)
    d.line([(71,145),(42,173),(71,201)],fill=ink,width=6)
    d.line([(42,173),(101,173)],fill=ink,width=6)
    d.ellipse((125,115,226,217),fill="#7784a0")
    d.ellipse((166,135,190,165),fill="#33415b")
    d.ellipse((148,164,205,206),fill="#33415b")
    d.text((253,115),item.get("who","Друг"),font=f(39,True),fill=ink)
    d.text((253,168),"в сети",font=f(27),fill="#5c9ce8")
    for k in range(3):d.ellipse((1036,145+k*22,1046,155+k*22),fill=ink)
    d.rounded_rectangle((442,258,638,315),radius=28,fill="#bbc8d1" if light else "#293648")
    d.text((471,266),"Сегодня",font=f(30),fill="#1e2834" if light else "white")
    size=35
    linesets=[wrap(d,txt,f(size),850) for txt in item["lines"]]
    total=sum(28+len(x)*51+42 for x in linesets)+(len(linesets)-1)*18
    if total>840:
        size=32
        linesets=[wrap(d,x,f(size),860) for x in item["lines"]]
        total=sum(24+len(x)*47+42 for x in linesets)+(len(linesets)-1)*14
    if total>840:raise RuntimeError("Reject overlong chat: would overlap composer")
    y=338
    for i,lines in enumerate(linesets):
        side="in" if i%2==0 else "out"
        lh=51 if size==35 else 47
        h=28+len(lines)*lh+42
        maxlen=max(d.textlength(line,font=f(size)) for line in lines)
        w=min(942,max(290,int(maxlen+82)))
        x=24 if side=="in" else W-w-24
        bubble=incoming if side=="in" else outgoing
        d.rounded_rectangle((x,y,x+w,y+h),radius=29,fill=bubble)
        if side=="in":d.polygon([(x+15,y+h-22),(x-7,y+h+1),(x+46,y+h-10)],fill=bubble)
        else:d.polygon([(x+w-15,y+h-22),(x+w+7,y+h+1),(x+w-45,y+h-10)],fill=bubble)
        tc="#1c2633" if light else "white"
        for j,line in enumerate(lines):d.text((x+33,y+17+j*lh),line,font=f(size),fill=tc)
        stamp="18:"+str(42+i).zfill(2)
        d.text((x+w-(124 if side=="out" else 79),y+h-35),stamp,font=f(19),fill="#7f8c98" if light else "#cad7e6")
        if side=="out":
            for off in (34,24):d.line([(x+w-off-12,y+h-25),(x+w-off-5,y+h-18),(x+w-off+9,y+h-34)],fill="#729e90" if light else "#dceaff",width=2)
        y+=h+(18 if size==35 else 14)
    d.rectangle((0,1198,W,1307),fill=top)
    d.ellipse((29,1226,88,1284),outline="#8b9baa",width=5)
    d.text((136,1236),"Сообщение",font=f(37),fill="#8696a8")
    d.ellipse((1016,1227,1046,1274),outline="#8b9baa",width=4)
    d.rounded_rectangle((1028,1218,1036,1261),radius=4,fill="#8b9baa")
    d.rounded_rectangle((428,1327,652,1335),radius=5,fill="#abb4be")
    im.save(path,format="PNG",optimize=True)

def threads_image(item,path):
    dark=int(item["id"][-2:])%3==0
    bg="#101113" if dark else "#ffffff"
    ink="#fbfbfb" if dark else "#191919"
    dline="#303134" if dark else "#e8e8e8"
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im)
    d.text((52,31),"18:47",font=f(32,True),fill=ink)
    d.text((845,37),"LTE",font=f(25),fill=ink)
    d.rounded_rectangle((966,33,1043,73),radius=7,outline=ink,width=3)
    d.rounded_rectangle((974,41,1028,65),radius=4,fill=ink)
    d.text((45,115),"←",font=f(48),fill=ink)
    d.text((441,125),"Threads",font=f(39,True),fill=ink)
    d.line([(0,224),(W,224)],fill=dline,width=3)
    d.ellipse((45,274,132,360),fill="#a3b1ba" if dark else "#7788ad")
    d.text((77,287),item["who"][0].upper(),font=f(43,True),fill="#ffffff")
    d.text((159,275),item["who"],font=f(32,True),fill=ink)
    d.text((930,283),"4 ч.",font=f(24),fill="#8d9298")
    d.text((1010,278),"···",font=f(38),fill=ink)
    txtsize=49
    lines=wrap(d,item["text"],f(txtsize),875)
    if len(lines)>9:txtsize=44;lines=wrap(d,item["text"],f(txtsize),885)
    if len(lines)>10:raise RuntimeError("Reject overlong Threads text")
    for i,line in enumerate(lines):d.text((158,391+i*72),line,font=f(txtsize),fill=ink)
    y=417+len(lines)*72
    d.text((160,y),"♡     ◯     ↗     ⋯",font=f(42),fill=ink)
    d.line([(40,1100),(W-40,1100)],fill=dline,width=2)
    d.line([(55,1182),(93,1148),(132,1182),(132,1210),(55,1210),(55,1182)],fill=ink,width=5)
    d.ellipse((282,1152,331,1201),outline=ink,width=5)
    d.line([(322,1195),(348,1222)],fill=ink,width=5)
    d.rounded_rectangle((508,1150,577,1214),radius=16,outline=ink,width=5)
    d.line([(543,1167),(543,1199)],fill=ink,width=5)
    d.line([(525,1183),(561,1183)],fill=ink,width=5)
    d.line([(739,1170),(760,1152),(783,1171),(806,1152),(831,1172),(783,1222),(739,1170)],fill=ink,width=5)
    d.ellipse((971,1149,1007,1186),outline=ink,width=5)
    d.arc((949,1180,1030,1231),185,355,fill=ink,width=5)
    d.rounded_rectangle((430,1327,650,1335),radius=4,fill="#aeb2b7")
    im.save(path,format="PNG",optimize=True)

def get_all_posts(token):
    h={"Authorization":"Bearer "+token}
    rows=[];cur=None
    for page in range(150):
        url=BASE+"/posts"+("?cursor="+quote(cur,safe="") if cur else "")
        r=requests.get(url,headers=h,timeout=40)
        if r.status_code!=200:raise RuntimeError("Cannot read posts: HTTP "+str(r.status_code))
        obj=r.json();data=obj.get("data",[]);meta=obj.get("meta",{})
        if isinstance(data,dict):data=data.get("items",data.get("posts",[]))
        if not isinstance(data,list):raise RuntimeError("Unexpected posts response")
        rows.extend(data)
        nxt=meta.get("next_cursor")
        if not nxt:
            if meta.get("has_more"):raise RuntimeError("Pagination incomplete: stop")
            return rows
        if nxt==cur:raise RuntimeError("Pagination cursor did not advance")
        cur=nxt
    raise RuntimeError("Too many VediSMM pages: stop")

def schedule_one(token,item,when,path):
    h={"Authorization":"Bearer "+token}
    with open(path,"rb") as img:
        r=requests.post(BASE+"/media",headers=h,files={"file":(item["id"]+".png",img,"image/png")},timeout=95)
    if r.status_code!=201:raise RuntimeError("Media HTTP "+str(r.status_code))
    media=r.json()["data"];mid=int(media.get("id") or 0)
    if mid<1 or media.get("status")!="ready" or media.get("type")!="image":
        raise RuntimeError("Image not ready; no draft")
    title="DVOIQ / "+item["id"]+" / "+when.strftime("%Y-%m-%d")
    key="dvoiq-scheduled-"+hashlib.sha256((title+str(ACCOUNT)).encode()).hexdigest()[:40]
    r=requests.post(BASE+"/posts",headers={**h,"Idempotency-Key":key},json={"title":title,"content":"","account_ids":[ACCOUNT],"media_ids":[mid]},timeout=45)
    if r.status_code!=201:raise RuntimeError("Draft HTTP "+str(r.status_code)+" "+r.text[:180])
    obj=r.json()["data"];pid=int(obj.get("id") or 0)
    if pid<1 or obj.get("status")!="draft" or not obj.get("media") or not r.headers.get("ETag"):
        raise RuntimeError("VediSMM draft not confirmed")
    at=when.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
    sr=requests.post(BASE+"/posts/"+str(pid)+"/schedule",headers={**h,"If-Match":r.headers["ETag"]},json={"scheduled_at":at},timeout=45)
    if sr.status_code!=200:raise RuntimeError("Schedule HTTP "+str(sr.status_code)+" "+sr.text[:180])
    saved=sr.json()["data"]
    if saved.get("status")!="scheduled" or int(saved.get("id") or 0)!=pid:
        raise RuntimeError("VediSMM schedule not confirmed")
    return {"id":item["id"],"post_id":pid,"scheduled_at":at}

def run(preview=False):
    bank=json.loads(BANK.read_text(encoding="utf-8"))
    if len(set(a["id"] for a in bank))!=len(bank):raise RuntimeError("Duplicate editorial IDs")
    chats=[a for a in bank if a["type"]=="telegram"]
    threads=[a for a in bank if a["type"]=="threads"]
    ordered=[]
    while chats or threads:
        ordered+=chats[:2];del chats[:2]
        if threads:ordered.append(threads.pop(0))
    if preview:
        Path("dvoiq_previews").mkdir(exist_ok=True)
        for item in ordered[:6]:
            fn="dvoiq_previews/"+item["id"]+".png"
            (chat_image if item["type"]=="telegram" else threads_image)(item,fn)
        print(json.dumps({"status":"preview_only","made":min(6,len(ordered)),"bank":len(bank)},ensure_ascii=False))
        return
    token=__import__("os").environ.get("VEDISMM_TOKEN","").strip()
    if not token:raise RuntimeError("No VEDISMM_TOKEN; stop")
    a=requests.get(BASE+"/accounts",headers={"Authorization":"Bearer "+token},timeout=35)
    if a.status_code!=200:raise RuntimeError("Account HTTP "+str(a.status_code))
    data=a.json().get("data",[])
    m=[v for v in data if v.get("network")=="vk" and str(v.get("external_id","")).lstrip("-")==GROUP]
    if len(m)!=1 or int(m[0].get("id") or 0)!=ACCOUNT:
        raise RuntimeError("DVOIQ account verification failed; nothing written")
    posts=get_all_posts(token)
    own=[p for p in posts if ACCOUNT in [int(x) for x in p.get("account_ids",[]) if str(x).isdigit()]]
    used=set()
    for p in own:
        title=p.get("title") or ""
        if title.startswith("DVOIQ / "):
            bits=title.split(" / ")
            if len(bits)>=3 and p.get("status") not in ("deleted","failed"):
                used.add(bits[1])
    now=datetime.now(TZ);today=now.date();dkey=today.isoformat()
    already=sum(1 for p in own if p.get("status") in ("scheduled","published","queued") and (
        dkey in str(p.get("scheduled_at") or "") or
        dkey in str(p.get("published_at") or "") or
        (p.get("title") or "").endswith(" / "+dkey)))
    if already>=10:
        print(json.dumps({"status":"cap_reached","already":already,"date":dkey}));return
    places=[datetime.combine(today,dt_time(h,m),tzinfo=TZ) for h,m in SLOTS]
    available=[a for a in ordered if a["id"] not in used]
    results=[]
    for when in places:
        if already+len(results)>=10:break
        if when<=now+timedelta(minutes=40):continue
        if not available:break
        item=available.pop(0)
        Path("dvoiq_output").mkdir(exist_ok=True)
        dest="dvoiq_output/"+item["id"]+".png"
        (chat_image if item["type"]=="telegram" else threads_image)(item,dest)
        rec=schedule_one(token,item,when,dest)
        results.append(rec)
        print(json.dumps({"scheduled":rec},ensure_ascii=False),flush=True)
    out={"status":"scheduled" if results else "no_new_approved_slots",
         "date":dkey,"scheduled":results,"already":already,
         "remaining_ideas":len(available)}
    Path("dvoiq_daily_result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    try:run(preview=args.preview)
    except Exception as e:
        print("DVOIQ safely stopped: "+str(e),flush=True)
        sys.exit(1)
