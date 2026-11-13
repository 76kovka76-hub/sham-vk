"""SKRBL: free AI Horde four-panel pencil-comic trial.

One-off generation uses the same free generator planned for automation; unlike
previous ChatGPT-generated post this trial does NOT call paid/ChatGPT image APIs.
Posting is only permitted by explicit GitHub test commit marker and only for
SKRBL 243241856. Publication requires all four frames to complete.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import random
import time

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops, ImageStat
import requests

from publish_test import BASE, _data, _target_account, _valid_vk_url

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "free_comic_trial.png"
INFO = ROOT / "free_comic_trial.json"
SEED = "skrbl-free-trial-20261113-001"
CAPTION = ("Открыл рабочую почту на минутку. Письма вылезли из экрана и начали "
           "ставить мне дедлайны. Бл***ь, больше ни один понедельник меня не увидит. "
           "\n\n#SKRBL #юмор #карандашныемемы")

# Four connected scenes of an original, hard-hitting work-horror joke.
PANELS = [
    {
        "top": "РЕШИЛ ПРОВЕРИТЬ ПОЧТУ...",
        "prompt": "In a messy home office, a scruffy exhausted adult man with messy black spiky hair, round large nose, crooked teeth, striped blue pajamas and a coffee mug, casually opening work email on laptop, tired but hopeful face, desk piled with papers, alarm clock, desk lamp and socks, funny mundane slice-of-life situation"
    },
    {
        "top": "347 ПИСЕМ. ВСЕ «СРОЧНО».",
        "prompt": "Same scruffy adult man with messy black spiky hair, round large nose, crooked teeth, striped blue pajamas, at same cluttered desk, eyes comically bulging out in horror as laptop erupts with a ridiculous avalanche of hundreds of paper envelopes, coffee cup tipping over, arms raised, visual slapstick exaggerated surprised face"
    },
    {
        "top": "ПИСЬМА НАЧАЛИ МЕНЯ ЖРАТЬ!",
        "prompt": "Same scruffy adult man with messy black spiky hair, round large nose, crooked teeth, striped blue pajamas, running in utter panic from an absurd swarm of living angry paper envelopes with teeth and tiny arms, home office destroyed, papers flying, coffee splashing, hilariously frantic physical comedy, dynamic wide scene"
    },
    {
        "top": "БЛ***Ь. НА*** Я ЕЁ ОТКРЫЛ?!",
        "prompt": "Same scruffy adult man with messy black spiky hair, round large nose, crooked teeth, striped blue pajamas, hiding under desk with terrified tired bloodshot eyes and frazzled hair, holding empty coffee mug, angry monster envelopes climbing out from laptop and searching for him, funny dark office absurdist humor, scattered papers, dramatic slapstick finale"
    },
]
assert len(PANELS) == 4

PAPER = (248, 246, 237)
STROKE = (37, 34, 33)
BLUE = (103, 128, 174)


def _font(size):
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ]
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _convert_to_pencil(im, panel_size=(696, 527)):
    """Make the *generated* scene look like graphite on rough off-white paper."""
    im = ImageOps.fit(im.convert("RGB"), panel_size, method=Image.Resampling.LANCZOS)
    grey = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    blurred = ImageOps.invert(grey).filter(ImageFilter.GaussianBlur(11))
    dodge = ImageChops.divide(grey, ImageOps.invert(blurred), scale=236)
    edges = ImageOps.autocontrast(grey.filter(ImageFilter.FIND_EDGES), cutoff=3)
    edges = ImageOps.invert(edges)
    edges = edges.point(lambda x: min(255, int(x*0.92 + 11)))
    pencil = ImageChops.darker(dodge, edges)
    pencil = ImageOps.autocontrast(pencil, cutoff=1)
    pencil = pencil.point(lambda x: min(255, int(x * 0.71 + 73)))
    # Warm ink-on-paper instead of generic grayscale photography.
    return ImageOps.colorize(pencil, black="#302c2a", white="#fcfaf2").convert("RGB")


def _text_center(draw, text, y, box, max_font=47, origin_x=0):
    for size in range(max_font, 20, -1):
        font = _font(size)
        if draw.textbbox((0,0), text, font=font, stroke_width=0)[2] <= box:
            break
    else:
        raise RuntimeError("SKRBL panel has overly long text")
    draw.text((origin_x+box//2, y), text, anchor="mt", font=font, fill=STROKE,
              stroke_width=0)
    return size


def _quality_gate(frames, pencil_frames):
    """Conservative machine checks; does NOT replace human visual editorial review."""
    if len(frames) != 4:
        raise RuntimeError("Four distinct panels required")
    if len({im.tobytes()[::211][:6000] for im in frames}) < 4:
        raise RuntimeError("Duplicate panel images")
    for i, im in enumerate(frames):
        if im.width < 384 or im.height < 384:
            raise RuntimeError("Free AI returned low-resolution frame")
        stat = ImageStat.Stat(im.convert("L"))
        if stat.stddev[0] < 32:
            raise RuntimeError(f"Panel {i+1} visually flat: rejected")
        penc = pencil_frames[i].convert("L")
        if ImageStat.Stat(penc).stddev[0] < 19:
            raise RuntimeError(f"Panel {i+1} pencil texture too flat: rejected")


def _make_panel_request(index, item):
    post = {"scene":"work", "topic":"skrbl_original_work_mail",
            "visual": (
                "Detailed four-panel narrative comic illustration. Single panel scene: "
                + item["prompt"]
                + ". Deliberately crude, quirky, hand-drawn amateur pencil cartoon with "
                "heavy scratchy black ink outlines and densely crosshatched shadows, "
                "ragged lines, messy graph paper texture, tiny comic details and fun "
                "background objects. Characters must have comically ugly expressive "
                "faces, giant uneven eyes, tiny tiny legs, funny dynamic gestures. "
                "Authentic handmade rough pencil scribble, NOT anime, NOT realistic "
                "photography, NOT 3D, NOT polished vector, no text, no watermarks."
            )}
    # AI Horde is a FREE volunteer-powered service. Use a direct tailored
    # pencil-art prompt: the general SHAM anime preset must NOT be used here.
    key = os.getenv("AIHORDE_API_KEY", "").strip() or "0000000000"
    headers = {"apikey": key,
        "Client-Agent":"SKRBL:1.0:https://github.com/76kovka76-hub/sham-vk"}
    prompt = post["visual"] + " ### " + (
        "color digital painting, anime, photorealistic face, glossy 3d, vector art, "
        "blurry, empty background, polished marketing illustration, captions, words, "
        "letters, font, logo, text, watermark, signature, nude, nsfw, extra arms"
    )
    params = {
        "width": 512, "height": 512, "steps": 24, "n":1,
        "cfg_scale": 7.5, "sampler_name": "k_euler_a",
        "seed": str(int(sha256(f"{SEED}-{index}".encode()).hexdigest()[:8],16))
    }
    payload={"prompt":prompt,"params":params,"nsfw":False,
             "censor_nsfw":True,"r2":True,"shared":False,
             "replacement_filter":True}
    api="https://aihorde.net/api/v2"
    req=requests.post(api+"/generate/async",headers=headers,json=payload,timeout=55)
    req.raise_for_status()
    reply=req.json()
    job=reply.get("id")
    if not isinstance(job,str) or not job:
        raise RuntimeError(f"AI Horde rejected panel {index+1}: {str(reply)[:200]}")
    end=time.monotonic()+475
    while time.monotonic()<end:
        time.sleep(11)
        check=requests.get(api+"/generate/check/"+job,timeout=40)
        check.raise_for_status()
        status=check.json()
        if status.get("faulted") or status.get("is_possible") is False:
            raise RuntimeError(f"AI Horde could not generate panel {index+1}")
        if not status.get("done"):
            continue
        result=requests.get(api+"/generate/status/"+job,timeout=45)
        result.raise_for_status()
        choices=result.json().get("generations") or []
        if not choices or choices[0].get("censored"):
            raise RuntimeError(f"AI Horde returned no safe image for panel {index+1}")
        g=choices[0]
        url=g.get("img")
        if not isinstance(url,str) or not url.startswith("https://"):
            raise RuntimeError("No approved HTTPS image URL")
        rr=requests.get(url,timeout=75)
        rr.raise_for_status()
        if len(rr.content)>16_000_000:
            raise RuntimeError("Generated frame too large")
        with Image.open(io.BytesIO(rr.content)) as img:
            output=img.convert("RGB")
        return index,output,{"model":g.get("model"),"job":job}
    try:
        requests.delete(api+"/generate/status/"+job,headers=headers,timeout=15)
    except requests.RequestException:
        pass
    raise RuntimeError(f"AI Horde free queue timeout for panel {index+1}")


def make_comic(frame_provider=None):
    """Build one 4-frame comic using an explicit image source.
    
    The caller decides between free providers; no implicit paid fallback.
    """
    if frame_provider is None:
        frame_provider = _make_panel_request
    if len(set(x["top"] for x in PANELS)) != 4:
        raise RuntimeError("Repeated panel lines")
    if CAPTION.count("#") != 3:
        raise RuntimeError("Caption must have three hashtags")
    ims = [None]*4
    metadata = [None]*4
    # Parallel volunteer-worker jobs, no fallback portrait or stock images.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(frame_provider, i, p)
                   for i,p in enumerate(PANELS)]
        for f in as_completed(futures):
            i, im, meta = f.result()
            ims[i] = im
            metadata[i] = meta
    drawings = [_convert_to_pencil(im) for im in ims]
    _quality_gate(ims, drawings)
    W, H, M, G = 1536, 1536, 30, 16
    PW = (W - 2*M - G)//2
    PH = (H - 2*M - G)//2
    img = Image.new("RGB", (W,H), PAPER)
    d=ImageDraw.Draw(img)
    rng=random.Random(800133)
    for i in range(27000):
        x=rng.randrange(W);y=rng.randrange(H)
        shade=rng.choice((221,226,235,243))
        d.point((x,y),fill=(shade,shade,shade-3))
    for i, (config, panel) in enumerate(zip(PANELS, drawings)):
        px=M+(i%2)*(PW+G)
        py=M+(i//2)*(PH+G)
        # High-contrast handwritten-style caption at top, action drawing below.
        d.rectangle((px,py,px+PW,py+PH),outline=STROKE,width=5,fill=PAPER)
        # Rough double border and imperfect pencil margins.
        d.line([(px+3,py+5),(px+PW-4,py+8)],fill=(85,75,75),width=2)
        d.line([(px+5,py+PH-9),(px+PW-6,py+PH-5)],fill=(99,91,89),width=2)
        text=config["top"]
        _text_center(d,text,py+20,PW,max_font=40,origin_x=px)
        # Character scenes occupy most of each panel.
        inner=ImageOps.fit(panel,(PW-12,PH-145),method=Image.Resampling.LANCZOS)
        img.paste(inner,(px+6,py+133))
        d.rectangle((px+5,py+133,px+PW-5,py+PH-5),outline=(80,76,72),width=2)
        # Scratchy pencil strike under each caption.
        for j in range(4):
            xx=px+10+rng.randrange(17)
            yy=py+110+j*3
            d.line([(xx,yy),(px+PW-11-rng.randrange(16),yy+rng.randrange(-3,4))],
                   fill=(175,166,150),width=1)
    # Small logo only; no photos or image generation in ChatGPT.
    d.text((W-41,H-14),"SKRBL",font=_font(20),fill=STROKE,anchor="rd")
    img.save(OUT,format="PNG",optimize=True)
    digest=sha256(OUT.read_bytes()).hexdigest()
    INFO.write_text(json.dumps({
        "style":"free_pencil_collage","panels":4,"sha256":digest,
        "size":[W,H],"captions":[p["top"] for p in PANELS],
        "models":[m.get("model") for m in metadata],
        "generated_by": metadata[0].get("provider", "AI Horde volunteer network"),
        "source_note":"free model; no automatic semantic visual QA",
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SKRBL_FREE_PREVIEW_READY:",OUT)
    print("SKRBL_COMIC_SHA256:",digest)
    print("SKRBL_MODEL_LIST:",[m.get("model") for m in metadata])
    return OUT


def publish(path):
    if os.getenv("SKRBL_ONE_OFF_PUBLISH")!="true":
        print("SKRBL_FREE_POST_OFF - preview saved but NOT published")
        return
    token=os.getenv("VEDISMM_TOKEN","").strip()
    if not token:
        raise RuntimeError("VEDISMM_TOKEN missing")
    headers={"Authorization":"Bearer "+token}
    account_id=_target_account(headers)
    print("SKRBL_SAFE_TARGET: 243241856",account_id)
    with path.open("rb") as fh:
        up=requests.post(BASE+"/media",headers=headers,
            files={"file":("SKRBL_free_pencil_comic.png",fh,"image/png")},
            timeout=90)
    media=_data(up,201)
    if media.get("type")!="image" or media.get("status")!="ready":
        raise RuntimeError("VediSMM did not confirm image")
    media_id=int(media["id"])
    if media_id<=0: raise RuntimeError("Invalid image ID")
    idem="skrbl-free-real-4panel-test-20261113-001"
    draft_resp=requests.post(BASE+"/posts",
        headers={**headers,"Idempotency-Key":idem},
        json={"title":"SKRBL: бесплатная генерация, тест карандашного комикса",
              "content":CAPTION,"account_ids":[account_id],"media_ids":[media_id]},
        timeout=45)
    draft=_data(draft_resp,201)
    if draft.get("status")!="draft" or not draft.get("media"):
        raise RuntimeError("Draft missing image")
    pid=int(draft.get("id") or 0); version=int(draft.get("version") or 0)
    if not (pid>0 and version>0):raise RuntimeError("Invalid draft version")
    jobresp=requests.post(BASE+f"/posts/{pid}/publish",
       headers={**headers,"Idempotency-Key":idem+"-publish"},
       json={"version":version},timeout=45)
    job=_data(jobresp,202)
    jid=job.get("id")
    if not isinstance(jid,str) or not jid:raise RuntimeError("No job ID")
    print("SKRBL_POST_ID:",pid)
    for attempt in range(24):
        time.sleep(5)
        res=_data(requests.get(BASE+"/jobs/"+jid,headers=headers,timeout=30),200)
        if res.get("status") in ("succeeded","partially_succeeded"):
            targets=[t for t in res.get("targets",[])
                if t.get("account",{}).get("id")==account_id
                and t.get("status")=="succeeded" and _valid_vk_url(t.get("external_url"))]
            if not targets:raise RuntimeError("Did not confirm delivery to SKRBL")
            print("SKRBL_FREE_PUBLISHED:",targets[0]["external_url"])
            return
        if res.get("status") in ("failed","cancelled"):
            raise RuntimeError(f"VediSMM job failed: {res.get('status')}")
    raise RuntimeError("No VK confirmation within 120s")


if __name__=="__main__":
    p=make_comic()
    publish(p)
