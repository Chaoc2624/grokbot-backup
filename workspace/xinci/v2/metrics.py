import csv
import io
import re
from datetime import datetime, timezone, timedelta

def parse_semrush_overview_csv(text) -> dict[str, dict]:
    if isinstance(text, dict):
        for k in ("output", "result", "data", "csv", "text", "body"):
            v = text.get(k)
            if isinstance(v, str) and v.strip():
                return parse_semrush_overview_csv(v)
            if isinstance(v, dict) and v is not text:
                got = parse_semrush_overview_csv(v)
                if got:
                    return got
        return {}
    if isinstance(text, list):
        return {}
    if not text or not str(text).strip():
        return {}
    text = str(text)
    
    f = io.StringIO(text.strip())
    # Try to sniff delimiter, default to semicolon based on prompt
    sample = f.read(2048)
    f.seek(0)
    
    delimiter = ";"
    if "," in sample and sample.count(",") > sample.count(";"):
        delimiter = ","
        
    reader = csv.DictReader(f, delimiter=delimiter)
    
    parsed = {}
    
    for row in reader:
        # Normalize keys by stripping and lowercasing
        norm_row = {k.strip().lower(): v for k, v in row.items() if k is not None}
        
        # Find keyword field
        kw_key = None
        for k in norm_row.keys():
            if "keyword" in k:
                kw_key = k
                break
        if not kw_key:
            continue
            
        keyword = norm_row[kw_key]
        if keyword is None:
            continue
        keyword = str(keyword).strip().lower()
        if not keyword:
            continue
            
        # Find fields
        vol_val = None
        for k in norm_row.keys():
            if "search volume" in k or k == "volume":
                vol_val = norm_row[k]
                break
                
        cpc_val = None
        for k in norm_row.keys():
            if "cpc" in k:
                cpc_val = norm_row[k]
                break
                
        comp_val = None
        for k in norm_row.keys():
            if "competition" in k:
                comp_val = norm_row[k]
                break
                
        res_val = None
        for k in norm_row.keys():
            if "result" in k:
                res_val = norm_row[k]
                break
                
        # Parse volume
        if vol_val is None or str(vol_val).strip() == "":
            volume = None
            nodata = True
        else:
            try:
                s_vol = str(vol_val).strip().replace(",", "")
                if s_vol == "" or s_vol.lower() == "none":
                    volume = None
                    nodata = True
                else:
                    f_vol = float(s_vol)
                    volume = int(f_vol)
                    nodata = False
            except (ValueError, TypeError):
                volume = None
                nodata = True
                
        # Parse cpc
        if cpc_val is None or str(cpc_val).strip() == "":
            cpc = None
        else:
            try:
                s_cpc = str(cpc_val).strip().replace(",", "").replace("$", "")
                if s_cpc == "" or s_cpc.lower() == "none":
                    cpc = None
                else:
                    cpc = float(s_cpc)
            except (ValueError, TypeError):
                cpc = None
                
        # Parse competition
        if comp_val is None or str(comp_val).strip() == "":
            competition = None
        else:
            try:
                s_comp = str(comp_val).strip().replace(",", "")
                if s_comp == "" or s_comp.lower() == "none":
                    competition = None
                else:
                    competition = float(s_comp)
            except (ValueError, TypeError):
                competition = None
                
        # Parse results
        if res_val is None or str(res_val).strip() == "":
            results = None
        else:
            try:
                s_res = str(res_val).strip().replace(",", "")
                if s_res == "" or s_res.lower() == "none":
                    results = None
                else:
                    results = int(float(s_res))
            except (ValueError, TypeError):
                results = None
                
        parsed[keyword] = {
            "volume": volume,
            "cpc": cpc,
            "competition": competition,
            "results": results,
            "nodata": nodata
        }
        
    return parsed

def parse_missing_as_nodata(phrases: list[str], parsed: dict[str, dict]) -> dict[str, dict]:
    result = dict(parsed)
    default_missing = {
        "volume": None,
        "cpc": None,
        "competition": None,
        "results": None,
        "nodata": True
    }
    for p in phrases:
        if p is None:
            continue
        key = str(p).strip().lower()
        if key not in result:
            result[key] = dict(default_missing)
    return result

def attach_provenance(obj: dict, source, region, collected_at, request_window, tool, extra=None) -> dict:
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz).isoformat()
    
    prov = {
        "source": source,
        "region": region,
        "collected_at": collected_at if collected_at is not None else now,
        "request_window": request_window,
        "tool": tool,
        "timezone": "Asia/Shanghai"
    }
    if extra is not None:
        prov["extra"] = extra
        
    obj["provenance"] = prov
    return obj

def classify_replication(items: list[dict]) -> dict:
    if not items:
        return {
            "distinct_authors": 0,
            "same_caption_ratio": 0.0,
            "tutorial_like": False,
            "video_semantics": "未核实",
            "independent_ugc": False
        }
        
    authors = set()
    captions = []
    tutorial_like = False
    
    tutorial_pattern = re.compile(r"tutorial|how to|how-to|教程|模板教程", re.IGNORECASE)
    
    video_verified_all = True
    
    for item in items:
        author = item.get("author") or item.get("owner")
        if author is not None:
            authors.add(str(author))
            
        caption = item.get("caption") or item.get("title") or item.get("text")
        if caption is not None:
            # normalize caption: lowercase, strip, collapse spaces
            norm_cap = re.sub(r'\s+', ' ', str(caption).strip().lower())
            captions.append(norm_cap)
            
        text_fields = [
            str(item.get("title", "")),
            str(item.get("caption", "")),
            str(item.get("text", ""))
        ]
        combined_text = " ".join(text_fields)
        if tutorial_pattern.search(combined_text):
            tutorial_like = True
            
        if item.get("video_verified") is not True:
            video_verified_all = False

    distinct_authors = len(authors)
    
    same_caption_ratio = 0.0
    if captions:
        from collections import Counter
        counts = Counter(captions)
        most_common_count = counts.most_common(1)[0][1]
        same_caption_ratio = float(most_common_count) / float(len(captions))
        
    video_semantics = "未核实"
    
    # independent_ugc True ONLY if video_verified is True AND distinct_authors>=2 AND same_caption_ratio < 0.5 AND not tutorial_like
    # Note: "video_verified is True" implies all or any? Usually implies all items or the aggregate. Let's check video_verified_all.
    independent_ugc = (
        video_verified_all is True and
        distinct_authors >= 2 and
        same_caption_ratio < 0.5 and
        not tutorial_like
    )
    
    return {
        "distinct_authors": distinct_authors,
        "same_caption_ratio": same_caption_ratio,
        "tutorial_like": tutorial_like,
        "video_semantics": video_semantics,
        "independent_ugc": independent_ugc
    }

def 立项_status(volume, kd, cpc, nodata=False, min_volume=500, max_kd=31) -> dict:
    if nodata or volume is None or kd is None or cpc is None:
        return {
            "layer": "验证",
            "status": "待验证",
            "passed_立项": False,
            "reason": "缺数不是0，不能判失败或通过"
        }
        
    try:
        vol_num = float(volume)
        kd_num = float(kd)
    except (ValueError, TypeError):
        return {
            "layer": "验证",
            "status": "待验证",
            "passed_立项": False,
            "reason": "缺数不是0，不能判失败或通过"
        }
        
    if vol_num >= min_volume and kd_num <= max_kd:
        return {
            "layer": "立项",
            "status": "过立项门槛",
            "passed_立项": True,
            "reason": f"Volume {vol_num} >= {min_volume} and KD {kd_num} <= {max_kd}"
        }
    else:
        return {
            "layer": "验证",
            "status": "未过立项门槛",
            "passed_立项": False,
            "reason": f"Volume {vol_num} (< {min_volume}) or KD {kd_num} (> {max_kd})"
        }
