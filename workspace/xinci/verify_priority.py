import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/workspace/xinci')
from v2.util import load_dotenv, today_bj, bj_stamp, save_json, load_json
from v2.budget import Ledger
from v2.aisa_client import AisaClient
from v2.metrics import parse_semrush_overview_csv, parse_missing_as_nodata, 立项_status, attach_provenance

def main():
    parser = argparse.ArgumentParser(description="Verify priority terms")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--date", default=today_bj(), help="Date string YYYY-MM-DD")
    parser.add_argument("--ledger", default="/workspace/xinci/v2_spend.json", help="Ledger path")
    parser.add_argument("--hard-cap", type=float, default=1.0, help="Hard cap USD")
    parser.add_argument("--today-prior", type=float, default=0.0, help="Today prior USD")
    parser.add_argument("--out", default=None, help="Output JSON file path")
    parser.add_argument("--anchor", default="gpts", help="Anchor keyword")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--max-terms", type=int, default=8, help="Max terms to process")
    
    args = parser.parse_args()
    
    load_dotenv()
    
    if not args.dry_run and not os.environ.get("AISA_API_KEY"):
        print("missing AISA_API_KEY", file=sys.stderr)
        sys.exit(2)

    # Initialize ledger
    ledger = Ledger(args.ledger, args.date, args.hard_cap, args.today_prior)
    if args.dry_run:
        os.environ["AISA_DRY_RUN"]="1"
    aisa = AisaClient(ledger)
    
    # Load input
    try:
        raw_input = load_json(args.input)
    except Exception as e:
        print(f"Error loading input JSON: {e}")
        raw_input = []
        
    if isinstance(raw_input, dict):
        # maybe wrapped
        items = raw_input.get("items", raw_input.get("terms", []))
        if not items and "phrase" in raw_input:
            items = [raw_input]
    elif isinstance(raw_input, list):
        items = raw_input
    else:
        items = []
        
    # Deduplicate unique phrases up to max-terms
    seen = set()
    unique_items = []
    for item in items:
        phrase = item.get("phrase") or item.get("keyword")
        if not phrase:
            continue
        p_lower = phrase.strip().lower()
        if p_lower not in seen:
            seen.add(p_lower)
            # Normalize item structure
            norm_item = {
                "phrase": phrase.strip(),
                "source": item.get("source", ""),
                "names": item.get("names", []),
                "evidence": item.get("evidence", "")
            }
            unique_items.append(norm_item)
            if len(unique_items) >= args.max_terms:
                break
                
    if not unique_items:
        print("No valid terms found in input.")
        output_data = {
            "date": args.date,
            "timestamp": bj_stamp(),
            "terms": []
        }
        out_path = args.out or f"verify-{args.date.replace('-', '')}.json"
        save_json(out_path, output_data)
        sys.exit(0)
        
    anchor = args.anchor
    locations = ["United States", "India"]
    
    # We will batch calls or make them per term
    # AisaClient.quote_and_use takes a list of {call_id, tool, arguments}
    calls = []
    call_map = {} # call_id -> (phrase, loc, type)
    
    call_counter = 1
    for item in unique_items:
        phrase = item["phrase"]
        for loc in locations:
            # 1. Trends call
            if ledger.remaining_usd < 0.01 and not args.dry_run:
                break
                
            keywords_list = [phrase, anchor] if phrase.lower() != anchor.lower() else [phrase]
            trends_args = {
                "body": [{
                    "keywords": keywords_list,
                    "location_name": loc,
                    "time_range": "past_7_days",
                    "item_types": ["google_trends_graph"]
                }]
            }
            t_id = f"t_{call_counter}"
            call_counter += 1
            calls.append({
                "call_id": t_id,
                "tool": "any_dataforseo_apis_v1_dataforseo_keywords_data_g_f56cfb",
                "arguments": trends_args
            })
            call_map[t_id] = (phrase, loc, "trends")
            
            # 2. Semrush overview call (db: us or in)
            db = "us" if loc == "United States" else "in"
            sem_args = {
                "phrase": phrase,
                "database": db
            }
            s_id = f"s_{call_counter}"
            call_counter += 1
            calls.append({
                "call_id": s_id,
                "tool": "get_semrush_keyword_overview",
                "arguments": sem_args
            })
            call_map[s_id] = (phrase, loc, "semrush_overview")

    results = {}
    if calls:
        try:
            # Check API key presence for live run
            if not args.dry_run and not os.environ.get("AISA_API_KEY") and not os.environ.get("AISA_API_BASE"):
                print("Error: AISA_API_KEY not found and not a dry-run.")
                sys.exit(2)
                
            # tool-router quote/use allow at most 20 calls per request
            responses = {}
            for i in range(0, len(calls), 20):
                batch = calls[i:i+20]
                part = aisa.quote_and_use(batch)
                if isinstance(part, dict):
                    responses.update(part)
                elif isinstance(part, list):
                    for resp in part:
                        if isinstance(resp, dict) and resp.get("call_id"):
                            responses[resp["call_id"]] = resp
            for c_id, resp in responses.items():
                if c_id in call_map:
                    phrase, loc, c_type = call_map[c_id]
                    if phrase not in results:
                        results[phrase] = {}
                    if loc not in results[phrase]:
                        results[phrase][loc] = {}
                    results[phrase][loc][c_type] = resp
        except Exception as e:
            print(f"API execution error: {e}")
            if not args.dry_run:
                sys.exit(2)

    raw_path = Path("/workspace/xinci/v2_run") / f"verify-raw-{args.date}.json"
    try:
        from v2.util import save_json as _save
        # do not include env; responses have data only
        _save(str(raw_path), {"date": args.date, "results": results})
        print("wrote", raw_path)
    except Exception as e:
        print("warn: could not save verify raw:", e)

    # Second pass for KD if volume >= 100 and not nodata
    kd_calls = []
    kd_map = {}
    for item in unique_items:
        phrase = item["phrase"]
        for loc in locations:
            db = "us" if loc == "United States" else "in"
            # check semrush overview result
            loc_res = results.get(phrase, {}).get(loc, {})
            sem_resp = loc_res.get("semrush_overview", {})
            # parse semrush overview to check volume and nodata
            # sem_resp might be raw text or dict containing 'result' or 'output'
            output_content = sem_resp.get("output") or sem_resp.get("result") or sem_resp
            parsed_overview = parse_semrush_overview_csv(output_content)
            
            # Check volume & nodata
            nodata = parse_missing_as_nodata(output_content)
            volume = None
            if not nodata and isinstance(parsed_overview, dict):
                volume = parsed_overview.get("volume") or parsed_overview.get("search_volume")
                try:
                    if volume is not None:
                        volume = float(volume)
                except:
                    volume = None
            
            if not nodata and volume is not None and volume >= 100:
                if ledger.remaining_usd >= 0.01 or args.dry_run:
                    kd_id = f"kd_{call_counter}"
                    call_counter += 1
                    kd_args = {
                        "phrase": phrase,
                        "database": db
                    }
                    kd_calls.append({
                        "call_id": kd_id,
                        "tool": "get_semrush_keyword_difficulty",
                        "arguments": kd_args
                    })
                    kd_map[kd_id] = (phrase, loc)

    if kd_calls:
        try:
            kd_responses = aisa.quote_and_use(kd_calls)
            for resp in kd_responses:
                c_id = resp.get("call_id")
                if c_id in kd_map:
                    phrase, loc = kd_map[c_id]
                    if phrase not in results:
                        results[phrase] = {}
                    if loc not in results[phrase]:
                        results[phrase][loc] = {}
                    results[phrase][loc]["semrush_kd"] = resp
        except Exception as e:
            print(f"KD API execution error: {e}")

    # Assemble final output terms
    output_terms = []
    for item in unique_items:
        phrase = item["phrase"]
        term_data = {
            "phrase": phrase,
            "source": item["source"],
            "names": item["names"],
            "evidence": item["evidence"],
            "metrics": {}
        }
        
        us_metrics = {}
        for loc in locations:
            loc_key = "US" if loc == "United States" else "IN"
            loc_res = results.get(phrase, {}).get(loc, {})
            
            # Parse trends leniently
            trends_resp = loc_res.get("trends", {})
            trends_out = trends_resp.get("output") or trends_resp.get("result") or trends_resp
            # Lenient trends parsing: if cannot find series, nodata True, values None, never 0
            trends_nodata = True
            trends_values = None
            try:
                # search json for google_trends_graph items
                if isinstance(trends_out, str):
                    try:
                        trends_out_json = json.loads(trends_out)
                    except:
                        trends_out_json = {}
                else:
                    trends_out_json = trends_out
                
                # navigate dataforseo structure
                tasks = trends_out_json.get("tasks", []) if isinstance(trends_out_json, dict) else []
                found_series = False
                for task in tasks:
                    result_list = task.get("result", [])
                    for res in result_list:
                        items_type = res.get("items", [])
                        for itm in items_type:
                            if itm.get("type") == "google_trends_graph":
                                # extract data points
                                data_points = itm.get("data", [])
                                if data_points:
                                    trends_nodata = False
                                    trends_values = data_points
                                    found_series = True
                            if found_series: break
                        if found_series: break
                    if found_series: break
            except Exception:
                pass
            
            # Parse semrush overview
            sem_resp = loc_res.get("semrush_overview", {})
            sem_out = sem_resp.get("output") or sem_resp.get("result") or sem_resp
            sem_nodata = parse_missing_as_nodata(sem_out)
            sem_parsed = parse_semrush_overview_csv(sem_out) if not sem_nodata else {}
            
            # Parse semrush kd
            kd_resp = loc_res.get("semrush_kd", {})
            kd_out = kd_resp.get("output") or kd_resp.get("result") or kd_resp
            kd_nodata = parse_missing_as_nodata(kd_out)
            kd_val = None
            if not kd_nodata:
                if isinstance(kd_out, dict):
                    kd_val = kd_out.get("keyword_difficulty") or kd_out.get("kd")
                elif isinstance(kd_out, (int, float)):
                    kd_val = kd_out
                else:
                    try:
                        kd_val = float(str(kd_out).strip())
                    except:
                        pass

            loc_metric = {
                "trends_nodata": trends_nodata,
                "trends_values": trends_values,
                "semrush_nodata": sem_nodata,
                "semrush_overview": sem_parsed,
                "kd_nodata": kd_nodata,
                "keyword_difficulty": kd_val
            }
            
            term_data["metrics"][loc_key] = loc_metric
            if loc_key == "US":
                us_metrics = loc_metric

        # 立项_status for US metrics
        us_vol = (us_metrics.get("semrush_overview") or {}).get("volume") if isinstance(us_metrics.get("semrush_overview"), dict) else None
        us_cpc = (us_metrics.get("semrush_overview") or {}).get("cpc") if isinstance(us_metrics.get("semrush_overview"), dict) else None
        us_kd = us_metrics.get("keyword_difficulty")
        us_nodata = bool(us_metrics.get("semrush_nodata")) or us_vol is None
        status_result = 立项_status(us_vol, us_kd, us_cpc, us_nodata)
        term_data["立项_status"] = status_result
        
        # Attach provenance
        attach_provenance(term_data, ledger)
        output_terms.append(term_data)

    final_output = {
    "date": args.date,
    "timestamp": bj_stamp(),
    "terms": output_terms
    }

    out_path = args.out or f"verify-{args.date.replace('-', '')}.json"
    save_json(out_path, final_output)
    print(f"Verification complete. Output saved to {out_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
