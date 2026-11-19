import re
from typing import List, Dict, Any, Set, Tuple

GENERIC_VIDEO_SEEDS: frozenset = frozenset([
    "capcut ai template",
    "ai photo to video",
    "capcut ai lab",
    "ai video trend",
    "capcut",
    "ai video",
    "ai template",
    "image to video",
    "photo to video",
    "how to use capcut",
    "best free ai image to video",
    "capcut 101"
])

PLACEHOLDER_DESC = "发现阶段，未做画面核验不得称独立成片"

def _normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip().lower()

# Long tutorial-title prefixes that should be treated as generic even with extra words
_GENERIC_TITLE_PREFIXES = (
    "how to use capcut",
    "capcut 101",
    "best free ai image to video",
    "how to use capcut's",
    "capcut templates:",
    "capcut ai video template program",
    "capcut ai video editing tutorial",
    "capcut ai avatar tutorial",
    "i tried every image to video",
    "top 5 free secret ai tools",
    "5 best free ai image to video",
    "3 best free ai image to video",
    "free image-to-video ai",
    "the new best 4 free ai video",
    "ai video generators ranked",
)

def is_generic_video_phrase(phrase: str) -> bool:
    if not phrase:
        return True
    norm = _normalize(phrase)
    if norm in GENERIC_VIDEO_SEEDS:
        return True
    # Do NOT treat "CapCut Peek AI" as generic just because it starts with "capcut "
    for prefix in _GENERIC_TITLE_PREFIXES:
        if norm == prefix or norm.startswith(prefix + " ") or norm.startswith(prefix):
            return True
    # Generic how-to / best-of listicles about the tool, not a named play
    if re.search(r"^(how to (use|make)|best |top \d+|\d+ best )", norm) and "capcut" in norm and "peek" not in norm and "jatayu" not in norm and "sheru" not in norm:
        return True
    return False

def _extract_text_fields(item: dict) -> str:
    parts = []
    for field in ["name", "title", "caption", "text"]:
        val = item.get(field)
        if val and isinstance(val, str):
            parts.append(val)
    desc = item.get("desc")
    if desc and isinstance(desc, str) and desc.strip() != PLACEHOLDER_DESC:
        parts.append(desc)
    return " ".join(parts)

def extract_video_keywords(items: list[dict]) -> dict:
    keywords_map: Dict[str, Dict[str, Any]] = {}
    query_anchors_map: Dict[str, Dict[str, Any]] = {}
    skipped_generic: List[Dict[str, Any]] = []
    
    for item in items:
        full_text = _extract_text_fields(item)
        if not full_text:
            continue
            
        url = item.get("url")
        platform = item.get("platform", "unknown")
        first_seen = item.get("first_seen")
        
        # Check for generic seeds usage as anchor
        lower_text = full_text.lower()
        for seed in GENERIC_VIDEO_SEEDS:
            if seed in lower_text:
                if seed not in query_anchors_map:
                    query_anchors_map[seed] = {
                        "keyword": seed,
                        "phrase": seed,
                        "source": "热梗轨",
                        "from": "extracted",
                        "role": "anchor",
                        "reason": "发现阶段，未做画面核验不得称独立成片",
                        "evidence": seed,
                        "names": [seed],
                        "urls": [],
                        "platforms": set(),
                        "first_seen": first_seen,
                        "tutorial_like": True,
                        "video_semantics": "未核实",
                        "independent_ugc": False
                    }
                if url and url not in query_anchors_map[seed]["urls"]:
                    query_anchors_map[seed]["urls"].append(url)
                if platform:
                    query_anchors_map[seed]["platforms"].add(platform)
                if first_seen and (not query_anchors_map[seed]["first_seen"] or first_seen < query_anchors_map[seed]["first_seen"]):
                    query_anchors_map[seed]["first_seen"] = first_seen

        # Specific pattern 1: Quoted or instructed CapCut AI Lab searches
        # e.g. 搜 "peek", type "rich", etc.
        qclass = r"[\"\u201c\u201d'\u2018\u2019]"
        search_patterns = [
            r"(?:搜|搜索|type|search|typed)\s*" + qclass + r"([^\"\u201c\u201d'\u2018\u2019]+)" + qclass,
            qclass + r"([^\"\u201c\u201d'\u2018\u2019]+)" + qclass + r"\s*(?:in the (?:ai )?(?:chat|lab)|ai|lab|trend|template|filter)",
        ]
        extracted_plays = []
        
        # Check explicit PEEK trend
        peek_m = re.search(r'([^\.\!\?\n]{0,80}\bpeek\b[^\.\!\?\n]{0,80})', full_text, re.IGNORECASE)
        if peek_m:
            tutorial_like = any(w in lower_text for w in ["how to", "tutorial", "tutorial-like", "教程", "步骤", "教你"])
            extracted_plays.append({
                "keyword": "CapCut Peek AI",
                "phrase": "CapCut Peek AI",
                "evidence": peek_m.group(1).strip(),
                "tutorial_like": tutorial_like,
                "reason_extra": "教程" if tutorial_like else ""
            })

        # Check Jatayu
        if re.search(r'\bjatayu\b', full_text, re.IGNORECASE):
            tutorial_like = any(w in lower_text for w in ["how to", "tutorial", "教程", "步骤"])
            evidence_match = re.search(r'([^\.\!\?\n]*jatayu[^\.\!\?\n]*)', full_text, re.IGNORECASE)
            evidence = evidence_match.group(1).strip() if evidence_match else "Jatayu"
            extracted_plays.append({
                "keyword": "Jatayu AI edit",
                "phrase": "Jatayu AI edit",
                "evidence": evidence,
                "tutorial_like": tutorial_like,
                "reason_extra": "教程" if tutorial_like else ""
            })

        # Check Sheru Bhai
        if re.search(r'sheru\s*bhai', full_text, re.IGNORECASE):
            tutorial_like = any(w in lower_text for w in ["how to", "tutorial", "教程", "步骤"])
            evidence_match = re.search(r'([^\.\!\?\n]*sheru\s*bhai[^\.\!\?\n]*)', full_text, re.IGNORECASE)
            evidence = evidence_match.group(1).strip() if evidence_match else "Sheru Bhai"
            extracted_plays.append({
                "keyword": "Sheru Bhai AI trend",
                "phrase": "Sheru Bhai AI trend",
                "evidence": evidence,
                "tutorial_like": tutorial_like,
                "reason_extra": "教程" if tutorial_like else ""
            })

        # Check general quoted search inside CapCut AI Lab context
        for pat in search_patterns:
            matches = re.findall(pat, full_text, re.IGNORECASE)
            for m in matches:
                token = m.strip()
                if token and len(token) < 30 and not is_generic_video_phrase(token):
                    norm_token = token.capitalize()
                    kw = f"CapCut {norm_token} AI"
                    tutorial_like = any(w in lower_text for w in ["how to", "tutorial", "教程", "步骤", "教你"])
                    evidence_match = re.search(rf'([^\.\!\?\n]*{re.escape(token)}[^\.\!\?\n]*)', full_text, re.IGNORECASE)
                    evidence = evidence_match.group(1).strip() if evidence_match else token
                    extracted_plays.append({
                        "keyword": kw,
                        "phrase": kw,
                        "evidence": evidence,
                        "tutorial_like": tutorial_like,
                        "reason_extra": "教程" if tutorial_like else ""
                    })

        for play in extracted_plays:
            kw = play["keyword"]
            if is_generic_video_phrase(kw):
                skipped_generic.append({"item": item, "phrase": kw, "reason": "generic seed or tool category"})
                continue
                
            if kw not in keywords_map:
                tutorial_str = "，属于教程类" if play["tutorial_like"] else ""
                reason = f"发现阶段，未做画面核验不得称独立成片{tutorial_str}"
                keywords_map[kw] = {
                    "keyword": kw,
                    "phrase": kw,
                    "source": "热梗轨",
                    "from": "extracted",
                    "role": "candidate",
                    "reason": reason,
                    "evidence": play["evidence"],
                    "names": [kw],
                    "urls": [],
                    "platforms": set(),
                    "first_seen": first_seen,
                    "tutorial_like": play["tutorial_like"],
                    "video_semantics": "未核实",
                    "independent_ugc": False
                }
            
            entry = keywords_map[kw]
            if url and url not in entry["urls"]:
                entry["urls"].append(url)
            if platform:
                entry["platforms"].add(platform)
            if first_seen and (not entry["first_seen"] or first_seen < entry["first_seen"]):
                entry["first_seen"] = first_seen

    # Post-process sets to lists
    final_keywords = []
    for kw, data in keywords_map.items():
        data["platforms"] = sorted(list(data["platforms"]))
        # Keep urls capped at a few examples
        data["urls"] = data["urls"][:5]
        final_keywords.append(data)

    final_anchors = []
    for anchor, data in query_anchors_map.items():
        data["platforms"] = sorted(list(data["platforms"]))
        data["urls"] = data["urls"][:5]
        final_anchors.append(data)

    notes = ""
    if not final_keywords:
        notes = "No specific deliverable video-trend keyword could be justified; video slots should stay empty."
    else:
        notes = f"Extracted {len(final_keywords)} specific deliverable video keyword candidates successfully."

    return {
        "keywords": final_keywords,
        "query_anchors": final_anchors,
        "skipped_generic": skipped_generic,
        "notes": notes
    }
