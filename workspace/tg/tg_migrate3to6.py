#!/usr/bin/env python3
"""Turn a day's old 3-hour digests into the fixed 6-hour board blocks.

  tg_migrate3to6.py --date 2026-10-08 --dry-run   # show what would happen; touches nothing
  tg_migrate3to6.py --date 2026-10-08             # do it

Steps (real run):
  1. move legacy digests/<date>/HH-HH.json (3h windows) into digests/<date>/3h/  (copy kept in archive/<date>.3h-legacy/)
  2. build every 6h block that has fragments with tg_merge6h (3h windows become the timeline sub-sections;
     hourly fragments, if any, win for their 3h sub-range), write digests/<date>/<block>.json and push it
  3. delete each old 3h window (00-03 ... 21-24) of that date from the board
daily.json is left alone.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import tg_merge6h as M
OLD = [M.lbl(h, h + 3) for h in range(0, 24, 3)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--date', required=True); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(); D = a.date; dd = M.ddir(D); dry = a.dry_run
    tag = '[dry-run] ' if dry else ''
    legacy = [p for p in sorted(glob.glob(os.path.join(dd, '*.json'))) if os.path.basename(p)[:-5] in OLD]
    # 1. move legacy 3h files
    if not dry:
        os.makedirs(os.path.join(dd, '3h'), exist_ok=True)
        arch = os.path.join(BASE, 'archive', D + '.3h-legacy'); os.makedirs(arch, exist_ok=True)
    for p in legacy:
        dst = os.path.join(dd, '3h', os.path.basename(p))
        if os.path.exists(dst) and not dry:
            print(f'{tag}keep existing {os.path.relpath(dst, BASE)}; archiving legacy {os.path.basename(p)} only')
            shutil.move(p, os.path.join(arch, os.path.basename(p))); continue
        print(f'{tag}move {os.path.relpath(p, BASE)} -> {os.path.relpath(dst, BASE)}')
        if not dry: shutil.copy2(p, arch); shutil.move(p, dst)
    # 2. build + push 6h blocks (in dry-run, fragments are read from their current location)
    built = []
    for b in M.BLOCKS:
        doc, missing = M.merge(D, *b)
        if doc is None: print(f'{tag}{D} {M.lbl(*b)}: no fragments, skipped'); continue
        path = os.path.join(dd, M.lbl(*b) + '.json')
        print(f"{tag}build {os.path.relpath(path, BASE)} partial={doc['partial']} missing_hours={missing} from {doc['sources']} "
              + ' '.join(f"{i['group']}={i['msg_count']}" for i in doc['items']))
        if not dry:
            json.dump(doc, open(path, 'w'), ensure_ascii=False, indent=1)
            M.push(path)
        built.append(M.lbl(*b))
    if not built: sys.exit('nothing built; old windows NOT deleted')
    # 3. delete old 3h windows from the board
    for w in OLD:
        print(f'{tag}board: delete {D} window {w}')
        if not dry:
            subprocess.run([sys.executable, os.path.join(BASE, 'tg_digest_push.py'), '--delete', D, '--window', w], check=True)

if __name__ == '__main__':
    main()
