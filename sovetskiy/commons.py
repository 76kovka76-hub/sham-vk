"""Fetch ONLY curator-approved public-domain Soviet film frames from Commons.

A Soviet release year by itself does not prove public-domain status.
No unapproved copyrighted modern movie/cartoon screenshots are downloaded.
"""
import io
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/"sources.json"
API="https://commons.wikimedia.org/w/api.php"
USER_AGENT="SOVETSKIY-VK/0.1 (source/rights audit; github.com/76kovka76-hub/sham-vk)"
ALLOWED_DOMAINS={"upload.wikimedia.org","commons.wikimedia.org"}

def catalog():
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data,list):
        raise ValueError("Bad SOVETSKIY source catalog")
    ids=set()
    for record in data:
        if not isinstance(record,dict) or not re.fullmatch(r"[a-z0-9_]{5,48}",record.get("id","")):
            raise ValueError("Unsafe image id")
        if record["id"] in ids:
            raise ValueError("Repeated source id")
        ids.add(record["id"])
        if record.get("rights")!="public_domain" or record.get("editor_approved") is not True:
            raise ValueError("Source must have an approved license first")
        title=record.get("file","")
        if not isinstance(title,str) or len(title)>130 or any(x in title for x in ("/","\\","\n")):
            raise ValueError("Unsafe Commons file title")
        proof=record.get("rights_proof")
        if not isinstance(proof,str) or not proof.startswith("https://commons.wikimedia.org/wiki/File:"):
            raise ValueError("Source license evidence required")
    return data


def get_record(source_id):
    return next((x for x in catalog() if x["id"]==source_id),None)


def _is_pd(ext):
    name=str((ext.get("LicenseShortName") or {}).get("value") or "").strip().lower()
    # Require machine-readable rights data, not merely a description.
    return name in ("public domain","cc0","cc0 1.0")


def download(source_id, session=requests):
    record=get_record(source_id)
    if record is None:
        raise RuntimeError("Unknown or unapproved Soviet frame: "+str(source_id))
    headers={"User-Agent": USER_AGENT,"Accept":"application/json"}
    q=session.get(API,
        params={"action":"query","titles":"File:"+record["file"],
                "prop":"imageinfo","iiprop":"url|size|extmetadata",
                "format":"json","formatversion":"2"},
        headers=headers,timeout=40)
    q.raise_for_status()
    pages=q.json().get("query",{}).get("pages",[])
    if not pages or len(pages)!=1:
        raise RuntimeError("Cannot validate Wikimedia Commons media metadata")
    info=(pages[0].get("imageinfo") or [])
    if not info or not _is_pd(info[0].get("extmetadata") or {}):
        raise RuntimeError("Commons does not confirm permitted public-domain status")
    url=info[0].get("url")
    parsed=urlparse(url or "")
    if parsed.scheme!="https" or parsed.hostname not in ALLOWED_DOMAINS:
        raise RuntimeError("Untrusted source host")
    if int(info[0].get("size") or 0)>12_000_000:
        raise RuntimeError("SOVETSKIY movie still exceeds size limit")
    fetched=session.get(url,headers={"User-Agent":USER_AGENT},timeout=60)
    fetched.raise_for_status()
    final=urlparse(fetched.url)
    if final.scheme!="https" or final.hostname not in ALLOWED_DOMAINS:
        raise RuntimeError("Untrusted redirect host")
    raw=fetched.content
    if not (5000<=len(raw)<=12_000_000):
        raise RuntimeError("Media size invalid")
    with Image.open(io.BytesIO(raw)) as pic:
        if pic.format not in ("PNG","JPEG","WEBP") or min(pic.size)<220:
            raise RuntimeError("Source is not a usable image")
        picture=ImageOps.exif_transpose(pic).convert("RGB")
    return picture,record
