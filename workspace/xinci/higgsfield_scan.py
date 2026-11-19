import os
import sys
import time
import argparse
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

sys.path.insert(0, '/workspace/xinci')
from v2.util import today_bj, bj_stamp, load_json, save_json, now_bj
from v2.snapshots import sitemap_diff, scrape_status

SITEMAPS = {
    "effects": "https://higgsfield.ai/effects/sitemap.xml",
    "apps": "https://higgsfield.ai/apps/sitemap.xml",
    "motion": "https://higgsfield.ai/motion/sitemap.xml",
    "mixed-media-presets": "https://higgsfield.ai/mixed-media-presets/sitemap.xml"
}

ALLOWED_PREFIXES = ("/effects/", "/apps/", "/motion/", "/mixed-media-presets/")
EXCLUDE_PREFIXES = (
    "/effects/use/",
    "/es/", "/ko/", "/ja/", "/de/", "/zh/",
    "/auth/", "/me/", "/payment/", "/login/", "/signin/", "/library/", "/share/", "/asset/", "/enterprise-studio"
)

SNAPSHOT_PATH = "/workspace/xinci/track_state/sitemaps/higgsfield.json"

def fetch_sitemap(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "xinci-higgsfield-scan/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read()
    
    urls_dict = {}
    root = ET.fromstring(content)
    
    # Handle namespaces
    ns = {}
    if root.tag.startswith('{'):
        ns_uri = root.tag.split('}')[0].strip('{')
        ns = {'ns': ns_uri}
        url_elements = root.findall('ns:url', ns)
    else:
        url_elements = root.findall('url')
        
    for uelem in url_elements:
        loc_el = uelem.find('ns:loc', ns) if ns else uelem.find('loc')
        if loc_el is None or not loc_el.text:
            continue
        loc = loc_el.text.strip()
        parsed = urlparse(loc)
        path = parsed.path
        
        # Validation checks
        if not any(path.startswith(p) for p in ALLOWED_PREFIXES):
            continue
        if any(path.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
            
        lastmod_el = uelem.find('ns:lastmod', ns) if ns else uelem.find('lastmod')
        lastmod = lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None
        
        urls_dict[loc] = {"sitemap_lastmod": lastmod} if lastmod else {}
        
    return urls_dict

def slug_to_name(slug):
    parts = [p for p in slug.split('/') if p]
    if not parts:
        return "Higgsfield"
    raw = parts[-1]
    cleaned = raw.replace('-', ' ').replace('_', ' ').strip()
    if not cleaned:
        return "Higgsfield"
    return cleaned.title()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date string YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", help="Output JSON path")
    args = parser.parse_args()

    date_str = args.date if args.date else today_bj()
    out_path = args.out if args.out else f"higgsfield-{date_str.replace('-', '')}.json"

    old_snapshot = load_json(SNAPSHOT_PATH, {})
    new_snapshot_sections = {}
    
    all_sections_failed = True
    total_now_count = 0
    total_new_count = 0
    any_error = False
    
    items = []
    keywords = []
    coverage = {}
    section_diffs = {}

    for i, (sec_name, url) in enumerate(SITEMAPS.items()):
        if i > 0:
            time.sleep(2.0)
            
        old_sec_data = old_snapshot.get(sec_name, {})
        old_urls_map = old_sec_data.get("urls", {})
        if isinstance(old_urls_map, list):
            # Backward compatibility if it was a list
            old_urls_map = {u: {} for u in old_urls_map}
            
        fetched_urls = None
        error_msg = None
        
        try:
            fetched_urls = fetch_sitemap(url)
            all_sections_failed = False
        except Exception as e:
            error_msg = str(e)
            any_error = True

        if fetched_urls is None:
            # Keep old snapshot for this section
            new_snapshot_sections[sec_name] = old_sec_data
            current_urls_for_diff = old_urls_map
            diff_res = sitemap_diff(list(old_urls_map.keys()) if old_urls_map else None, list(old_urls_map.keys()))
            diff_res["note"] = f"Fetch failed: {error_msg}"
            section_diffs[sec_name] = diff_res
            coverage[sec_name] = {
                "now_count": len(old_urls_map),
                "new_count": 0,
                "first_run": diff_res.get("first_run", False)
            }
            total_now_count += len(old_urls_map)
        else:
            all_sections_failed = False
            now_list = list(fetched_urls.keys())
            old_list = list(old_urls_map.keys()) if old_urls_map else None
            
            diff_res = sitemap_diff(old_list, now_list)
            section_diffs[sec_name] = diff_res
            
            new_snapshot_sections[sec_name] = {
                "urls": fetched_urls,
                "fetched_at": bj_stamp()
            }
            
            now_count = diff_res.get("now_count", len(now_list))
            new_count = diff_res.get("new_count", 0)
            first_run = diff_res.get("first_run", False)
            
            total_now_count += now_count
            total_new_count += new_count
            
            coverage[sec_name] = {
                "now_count": now_count,
                "new_count": new_count,
                "first_run": first_run
            }
            
            if not first_run and new_count > 0:
                for new_u in diff_res.get("new", []):
                    parsed = urlparse(new_u)
                    slug = parsed.path
                    name = slug_to_name(slug)
                    
                    item_entry = {
                        "name": name,
                        "url": new_u,
                        "desc": "Higgsfield 新增 (lastmod 不作发布日)",
                        "source": "Higgsfield",
                        "first_seen": bj_stamp(),
                        "is_new": True
                    }
                    meta = fetched_urls.get(new_u, {})
                    if meta.get("sitemap_lastmod"):
                        item_entry["sitemap_lastmod"] = meta["sitemap_lastmod"]
                    items.append(item_entry)
                    
                    kw_names = [name, f"{name} ai"]
                    for kw in kw_names:
                        if not any(k["name"].lower() == kw.lower() for k in keywords):
                            keywords.append({
                                "name": kw,
                                "source": "Higgsfield",
                                "first_seen": bj_stamp(),
                                "is_new": True
                            })

    if all_sections_failed and not old_snapshot:
        sys.exit(1)

    if not args.dry_run:
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        save_json(SNAPSHOT_PATH, new_snapshot_sections)

    had_error = any_error
    status = scrape_status(had_error, total_now_count, total_new_count)

    output_data = {
        "date": date_str,
        "tracks": {
            "higgsfield": {
                "items": items,
                "keywords": keywords
            }
        },
        "coverage": coverage,
        "first_run": any(v.get("first_run", False) for v in section_diffs.values()),
        "errors": [] if not any_error else ["Some sitemap fetches encountered errors"],
        "status": status
    }

    save_json(out_path, output_data)
    sys.exit(0)

if __name__ == "__main__":
    main()
