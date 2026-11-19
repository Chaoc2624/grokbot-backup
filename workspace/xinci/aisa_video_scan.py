import os
import sys
import argparse
import json
from datetime import datetime

sys.path.insert(0, "/workspace/xinci")
from v2.util import load_dotenv, now_bj, bj_stamp, today_bj, save_json
from v2.budget import Ledger
from v2.aisa_client import AisaClient
from v2.metrics import classify_replication, attach_provenance
from v2.extract_video import extract_video_keywords

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="AISA Video Scan")
    parser.add_argument("--date", default=today_bj())
    parser.add_argument("--ledger", default="/workspace/xinci/data/ledger.json")
    parser.add_argument("--hard-cap", type=float, default=2.0)
    parser.add_argument("--today-prior", type=float, default=0.0)
    parser.add_argument("--out", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-calls", type=int, default=50)
    parser.add_argument("--keep-raw", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["AISA_DRY_RUN"] = "1"

    if not args.dry_run and not os.environ.get("AISA_API_KEY"):
        print("AISA_API_KEY")
        sys.exit(2)

    date_str = args.date
    if not args.out:
        args.out = f"/workspace/xinci/meme-{date_str.replace('-', '')}.json"

    ledger = Ledger(
        path=args.ledger,
        date=date_str,
        hard_cap_usd=args.hard_cap,
        today_prior_usd=args.today_prior
    )

    client = AisaClient(ledger)

    ig_queries = ["CapCut AI template", "AI photo to video", "CapCut AI Lab", "AI video trend"]
    tt_queries = ["CapCut AI template", "AI photo to video"]
    yt_queries = ["CapCut AI template", "AI photo to video"]

    calls = []
    call_id_counter = 1

    ig_calls = []
    for q in ig_queries:
        if len(calls) >= args.max_calls:
            break
        cid = f"ig_{call_id_counter}"
        call_id_counter += 1
        ig_calls.append({
            "call_id": cid,
            "tool": "get_instagram_reels_search",
            "arguments": {"query": q, "date_posted": "last-week"}
        })
    
    tt_calls = []
    for q in tt_queries:
        if len(calls) + len(ig_calls) + len(tt_calls) >= args.max_calls:
            break
        cid = f"tt_{call_id_counter}"
        call_id_counter += 1
        tt_calls.append({
            "call_id": cid,
            "tool": "tiktok.search",
            "arguments": {"query": q, "datePosted": "this-week"}
        })

    yt_calls = []
    for q in yt_queries:
        if len(calls) + len(ig_calls) + len(tt_calls) + len(yt_calls) >= args.max_calls:
            break
        cid = f"yt_{call_id_counter}"
        call_id_counter += 1
        yt_calls.append({
            "call_id": cid,
            "tool": "get_youtube_search",
            "arguments": {"engine": "youtube", "q": q, "gl": "us", "hl": "en"}
        })

    collected_data = {}

    if ig_calls and ledger.remaining_usd > 0:
        res = client.quote_and_use(ig_calls)
        for k, v in res.items():
            if v.get("ok"):
                collected_data[k] = v.get("data")

    if tt_calls and ledger.remaining_usd > 0.02:
        res = client.quote_and_use(tt_calls)
        for k, v in res.items():
            if v.get("ok"):
                collected_data[k] = v.get("data")

    if yt_calls and ledger.remaining_usd > 0.02:
        res = client.quote_and_use(yt_calls)
        for k, v in res.items():
            if v.get("ok"):
                collected_data[k] = v.get("data")

    items = []
    raw_items = []

    def extract_list(data_obj):
        if isinstance(data_obj, list):
            return data_obj
        if isinstance(data_obj, dict):
            for key in ["reels", "items", "videos", "video_results", "data", "results"]:
                if key in data_obj and isinstance(data_obj[key], list):
                    return data_obj[key]
            for k, v in data_obj.items():
                if isinstance(v, list):
                    return v
        return []

    for cid, data in collected_data.items():
        platform = "instagram" if cid.startswith("ig") else ("tiktok" if cid.startswith("tt") else "youtube")
        lst = extract_list(data)
        for item in lst:
            if args.keep_raw:
                raw_items.append(item)
            
            author = item.get("author") or item.get("creator") or item.get("username") or item.get("channel")
            caption = item.get("caption") or item.get("title") or item.get("description") or ""
            url = item.get("url") or item.get("link") or item.get("webUrl")
            
            views = item.get("views") or item.get("view_count") or item.get("playCount")
            likes = item.get("likes") or item.get("like_count")

            if views is not None:
                try:
                    views = int(views)
                except:
                    views = None
            if likes is not None:
                try:
                    likes = int(likes)
                except:
                    likes = None

            name = (caption or "").strip().split("\n")[0][:80] or f"{platform} clip"
            replication_evidence = classify_replication([{"author": author, "caption": caption, "title": caption, "video_verified": False}])
            item_entry = {
                "name": name,
                "desc": "发现阶段，未做画面核验不得称独立成片",
                "source": "热梗轨",
                "url": url,
                "first_seen": bj_stamp(),
                "platform": platform,
                "metrics": {
                    "views": views,
                    "likes": likes
                },
                "replication_evidence": replication_evidence,
                "trend_stage": "发现",
                "video_semantics": "未核实",
                "coverage_type": "aisa_public"
            }
            items.append(item_entry)

    extracted = extract_video_keywords(items)
    keywords = extracted.get("keywords") or []
    # seeds stay anchors only; never copy them into board keywords
    query_anchors = extracted.get("query_anchors") or []

    output_data = {
        "tracks": {
            "meme": {
                "items": items,
                "keywords": keywords
            }
        },
        "query_anchors": query_anchors,
        "extraction_notes": extracted.get("notes"),
        "coverage": "aisa_public",
        "spend": {
            "actual_usd": ledger.actual_usd,
            "remaining_usd": ledger.remaining_usd
        },
        "notes": "Zero new items is zero_new not failure"
    }

    if args.keep_raw and raw_items:
        output_data["raw_items"] = raw_items

    save_json(args.out, output_data)
    print(json.dumps({"status": "success", "items_count": len(items), "spend": ledger.actual_usd, "remaining": ledger.remaining_usd}, ensure_ascii=False))
    sys.exit(0)

if __name__ == "__main__":
    main()
