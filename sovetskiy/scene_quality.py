"""SOVETSKIY editorial gate: a film frame MUST support its meme punchline.

Public-domain status proves nothing about comedic relevance. A specific frame
and its joke need a separate, explicit visual review. Never assume a Soviet
face fits any topical caption or that a generic mood label is proof.

All existing candidate pairs start 'pending'. Images must be actually viewed
before approval; image metadata and string similarity cannot do that.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MATCHES_PATH=ROOT/"scene_matches.json"


def load_matches():
    data=json.loads(MATCHES_PATH.read_text(encoding="utf-8"))
    if data.get("schema")!=1 or not isinstance(data.get("matches"),list):
        raise ValueError("Invalid SOVETSKIY visual review data")
    mapping={}
    for row in data["matches"]:
        key=row.get("joke_key","")
        if not isinstance(key,str) or not key or key in mapping:
            raise ValueError("Duplicate or invalid scene match key")
        mapping[key]=row
    return mapping


def review_info(joke,mapping=None):
    """Return verified approval metadata or raise; no optimistic fallbacks."""
    if mapping is None:
        mapping=load_matches()
    review=mapping.get(joke.key)
    if not isinstance(review,dict):
        raise ValueError("No visual review exists for the specific SOVETSKIY joke")
    if review.get("source_ids")!=list(joke.source_ids):
        raise ValueError("Frame IDs changed since visual review; approval invalid")
    if review.get("status")!="approved":
        raise ValueError("SOVETSKIY frame/joke pairing has not passed visual review")
    if not isinstance(review.get("reviewer"),str) or not review["reviewer"].strip():
        raise ValueError("Approved pairing lacks an editorial reviewer")
    note=review.get("expected_visual_story","")
    if not isinstance(note,str) or len(note.strip())<35:
        raise ValueError("No reason explaining how the visible scene supports the joke")
    observations=review.get("observed_per_frame")
    if (not isinstance(observations,list) or
        len(observations)!=len(joke.source_ids) or
        any(not isinstance(s,str) or len(s.strip())<25 for s in observations)):
        raise ValueError("Each frame needs an observed scene/gesture description")
    urls=review.get("reviewed_source_urls")
    if (not isinstance(urls,list) or len(urls)!=len(joke.source_ids) or
        any(not isinstance(u,str) or not u.startswith(
            "https://commons.wikimedia.org/wiki/File:") for u in urls)):
        raise ValueError("Review must point to each actually inspected source image")
    conclusion=review.get("review_note","")
    if not isinstance(conclusion,str) or len(conclusion.strip())<35:
        raise ValueError("Missing editor's explanation for the image/punchline match")
    return review


def is_approved(joke,mapping=None):
    try:
        review_info(joke,mapping)
        return True
    except ValueError:
        return False
