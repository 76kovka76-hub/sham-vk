"""SKRBL pencil-comic visual gags (100% local, free, reusable).

These are *comic elements*, not substitute scenes. Drawn over detailed free
image backgrounds to make the jokes visual instead of relying only on captions.
"""
import math
import random
from PIL import ImageDraw, ImageFont

INK=(34,30,28)
RED=(146,49,49)
PAPER=(250,247,235)
BLUE=(92,116,154)


def _line(d, coords, r, width=3, color=INK):
    """Imperfect sketch line, not a clean vector stroke."""
    out=[]
    a,b=coords
    n=max(3,int(math.dist(a,b)/8))
    for j in range(n+1):
        t=j/n
        jig=r.uniform(-1.65,1.65) if 0<j<n else 0
        out.append((a[0]+(b[0]-a[0])*t+jig,
                    a[1]+(b[1]-a[1])*t+jig))
    d.line(out,fill=color,width=width,joint="curve")


def _font(size):
    choices=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for f in choices:
        try:
            return ImageFont.truetype(f,size)
        except OSError:
            continue
    return ImageFont.load_default()


def hand_text(img,text,x,y,max_width,max_size=37,seed=0,color=INK):
    """Readable Cyrillic with intentionally uneven hand-inked baselines."""
    d=ImageDraw.Draw(img)
    r=random.Random(seed)
    font=None
    for size in range(max_size,17,-1):
        f=_font(size)
        width=d.textlength(text,font=f)
        if width<=max_width-20:
            font=f;break
    if font is None:
        raise ValueError("Text does not fit one panel")
    width=d.textlength(text,font=font)
    cursor=x+(max_width-width)/2
    for char in text:
        jitter=r.uniform(-2.5,2.5)
        d.text((round(cursor),round(y+jitter)),char,
               font=font,fill=color,stroke_width=0)
        cursor+=d.textlength(char,font=font)
    # Rough pencil underline: two irregular scribbles
    for k in range(2):
        a=(x+12+r.randint(0,13),y+max_size+8+k*3)
        b=(x+max_width-15-r.randint(0,13),y+max_size+7+k*4)
        _line(d,(a,b),r,width=1,color=(135,127,115))


def evil_letter(img, cx,cy,w,seed=0,red_stamp="СРОЧНО",scale=1):
    """Animated anthropomorphic bill/envelope with crooked angry face."""
    d=ImageDraw.Draw(img)
    r=random.Random(seed)
    h=int(w*0.69)
    x0,y0=cx-w//2,cy-h//2
    x1,y1=cx+w//2,cy+h//2
    # faint double hand-drawn ink border and off-white cut paper
    for off in (1,0):
        points=[
          (x0+3+off,y0+8),(x1-8,y0+2+off),
          (x1+off,y1-5),(x0-3,y1-2),
        ]
        d.polygon(points,fill=PAPER,outline=INK if off==0 else (117,107,96),width=3 if off==0 else 1)
    d.line([(x0,y0+6),(cx,y0+h*.47),(x1,y0+4)],fill=INK,width=3)
    d.line([(x0,y1-5),(cx,y0+h*.45),(x1,y1-5)],fill=(120,110,100),width=2)
    # angry eyebrows, furious eyes, toothy triangular mouth
    for dx in (-.20,.20):
        ex=int(cx+dx*w)
        ey=int(cy-h*.14)
        d.ellipse((ex-w*.115,ey-h*.13,ex+w*.115,ey+h*.11),
                  fill=(253,250,242),outline=INK,width=3)
        d.ellipse((ex-w*.04,ey-h*.03,ex+w*.035,ey+h*.055),fill=RED,outline=INK,width=2)
        _line(d,((ex-w*.13,ey-h*.22),(ex+w*.14,ey-h*.16 if dx<0 else ey-h*.26)),r,width=4)
    mx0,mx1=cx-w*.24,cx+w*.24
    mouth_y=cy+h*.19
    d.arc((mx0,mouth_y-h*.05,mx1,mouth_y+h*.35),start=0,end=180,fill=INK,width=4)
    for i in range(6):
        xx=mx0+(i+1)*(mx1-mx0)/7
        d.line((xx,mouth_y+h*.03,xx+w*.025,mouth_y+h*.12),fill=INK,width=2)
    # tiny waving arms and kicking legs
    arms=[
        ((x0,cy),(x0-w*.26,cy-h*.33)),
        ((x1,cy),(x1+w*.27,cy-h*.30)),
        ((cx-w*.22,y1),(cx-w*.30,y1+h*.30)),
        ((cx+w*.23,y1),(cx+w*.35,y1+h*.25))
    ]
    for a,b in arms:_line(d,(a,b),r,width=max(2,int(3*scale)))
    # red hand-stamped action cue instead of meaningless words
    small_font=_font(max(12,int(w*.082)))
    d.text((cx,cy+h*.28),red_stamp,anchor="mm",font=small_font,fill=RED,stroke_width=1,stroke_fill=PAPER)
    # haste speed lines
    for angle in (2.1,2.6,3.3,5.2,5.8):
        sx=cx+math.cos(angle)*w*.71
        sy=cy+math.sin(angle)*h*.88
        ex=sx+math.cos(angle)*w*.25
        ey=sy+math.sin(angle)*h*.3
        _line(d,((sx,sy),(ex,ey)),r,width=2)


def _panic_burst(img,cx,cy,rad,seed):
    d=ImageDraw.Draw(img)
    r=random.Random(seed)
    for i in range(20):
        angle=(i+r.random()*.2)*2*math.pi/20
        dx,dy=math.cos(angle),math.sin(angle)
        a=(cx+dx*rad,cy+dy*rad)
        b=(cx+dx*(rad+r.uniform(12,50)),cy+dy*(rad+r.uniform(12,55)))
        _line(d,(a,b),r,width=r.choice((2,3)),color=r.choice((INK,RED,INK)))


def decorate_email_comic(img,index,px,py,pw,ph):
    """Visual punchline overlays coordinated with our work-email story."""
    # Body starts at y+133; keep the caption area unobscured.
    if index==0:
        evil_letter(img, int(px+pw*.87),int(py+ph*.84),int(pw*.12),
                    seed=11,red_stamp="1")
    elif index==1:
        _panic_burst(img,px+pw*.5,py+ph*.56,pw*.19,seed=21)
        evil_letter(img,int(px+pw*.79),int(py+ph*.48),int(pw*.18),
                    seed=23,red_stamp="СРОЧНО")
        evil_letter(img,int(px+pw*.17),int(py+ph*.70),int(pw*.12),
                    seed=24,red_stamp="ДЕДЛАЙН")
    elif index==2:
        for i,(rx,ry,w) in enumerate(((.23,.43,.20),(.75,.63,.25),(.45,.79,.17),(.83,.34,.13))):
            evil_letter(img,int(px+pw*rx),int(py+ph*ry),int(pw*w),
                        seed=30+i,red_stamp=("СРОЧНО" if i%2==0 else "ВЧЕРА"))
        _panic_burst(img,px+pw*.5,py+ph*.67,pw*.26,seed=34)
    elif index==3:
        evil_letter(img,int(px+pw*.18),int(py+ph*.65),int(pw*.31),
                    seed=44,red_stamp="ВЧЕРА!!!")
        _panic_burst(img,px+pw*.3,py+ph*.60,pw*.19,seed=46)
    else:
        raise ValueError("Invalid 4-frame email comic index")
