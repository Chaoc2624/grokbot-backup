import os
sys = __import__('sys')
sys.path.insert(0, '/workspace/xinci')

import argparse
import subprocess
import time
from pathlib import Path
import json

from v2.util import today_bj, bj_stamp, load_json, save_json, load_dotenv
from v2.budget import Ledger
from v2.snapshots import report_is_current, classify_chart_items, write_game_snapshot, load_history
from v2.select_keywords import select_board_keywords
from v2.metrics import 立项_status
from v2.legacy_steps import new_coverage, set_step, run_legacy_sources, run_legacy_daily, run_finders, remaining_budget_usd, should_run_legacy_radar, blocked_unbounded_legacy_radar

def safe_copy(src, dst):
    """Copy src to dst unless they resolve to the same file."""
    import shutil
    s, d = Path(src), Path(dst)
    if not s.exists():
        return False
    d.parent.mkdir(parents=True, exist_ok=True)
    if s.resolve() == d.resolve():
        return False
    shutil.copy(s, d)
    return True


def run_cmd(argv, env=None, cwd=None):
    if cwd is None:
        cwd = os.environ.get('XINCI_SCRIPTS', '/workspace/xinci')
    merged_env = os.environ.copy()
    merged_env.setdefault('XINCI_HOME', merged_env.get('XINCI_HOME', cwd))
    if env:
        merged_env.update(env)
    start_t = time.time()
    p = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd,
        env=merged_env,
        bufsize=1
    )
    lines = []
    for line in p.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lines.append(line)
    p.wait()
    duration = time.time() - start_t
    tail = "".join(lines[-30:])
    return {"returncode": p.returncode, "tail": tail, "seconds": round(duration, 2)}


def _cov_existing(workdir, compact_date, slot, date_str):
    return {
        "track": workdir / f"tracks-{compact_date}-{slot}.json",
        "news": workdir / f"news-{compact_date}.json",
        "higgsfield": workdir / f"higgsfield-{compact_date}.json",
        "video": workdir / f"meme-{compact_date}.json",
        "verify": workdir / "v2_run" / f"verify-{date_str}.json",
        "doable": workdir / "v2_run" / f"doable-{date_str}.json",
    }


def _record_cov(coverage, name, steps_status, *, args, workdir, compact_date, slot, date_str):
    st = steps_status.get(name) or {}
    existing = _cov_existing(workdir, compact_date, slot, date_str)
    path = existing.get(name)
    reused = bool(path and path.exists())
    if st.get("skipped") or (isinstance(st, dict) and st.get("skipped") is True):
        reason = st.get("reason") or ""
        if "budget" in reason.lower() or "doable_budget" in str(st):
            set_step(coverage, name, "skipped_budget", reason or "budget remaining too low")
        elif getattr(args, "legacy_only", False) and reused:
            set_step(coverage, name, "cache_reuse", f"legacy-only: reuse already-captured {path.name}", {"path": str(path)})
        elif args.replay_dir:
            set_step(coverage, name, "skipped_replay", "offline fixture/replay; step not executed")
        elif args.no_paid and name in {"video", "verify", "doable"}:
            set_step(coverage, name, "skipped", "no-paid: paid AIsa step not executed")
        else:
            set_step(coverage, name, "skipped", reason or "skipped")
        return
    rc = st.get("returncode")
    if rc is None and st.get("status") in ("ok", "error"):
        set_step(coverage, name, "ok" if st.get("status") == "ok" else "failed", st.get("error") or "")
        return
    if rc == 0:
        set_step(coverage, name, "ok")
    else:
        set_step(coverage, name, "failed", f"exit {rc}")


def main():
    parser = argparse.ArgumentParser(description="Run v2 workflow")
    parser.add_argument("--date", default=today_bj())
    parser.add_argument("--slot", default="am", choices=["am", "pm"])
    parser.add_argument("--x-input", default=None)
    parser.add_argument("--xnew", default=None)
    parser.add_argument("--today-prior", type=float, default=0.0)
    parser.add_argument("--hard-cap", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip", default="")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--max-priority", type=int, default=8)
    parser.add_argument("--require-x", action="store_true")
    parser.add_argument("--workdir", default=None, help="Data root (default /workspace/xinci). Tests set this to a temp dir.")
    parser.add_argument("--replay-dir", default=None, help="Offline fixture/replay: reuse files here, skip live/paid scans. External I/O is mocked/skipped.")
    parser.add_argument("--no-paid", action="store_true", help="Skip paid AIsa steps (video/verify/doable use).")
    parser.add_argument("--legacy-only", action="store_true", help="Reuse today's already-collected files; only schedule missing legacy sources/daily/finders then merge/push.")
    args = parser.parse_args()

    scripts_home = Path("/workspace/xinci")
    workdir = Path(args.workdir or args.replay_dir or "/workspace/xinci").resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    os.environ["XINCI_HOME"] = str(workdir)
    os.environ["XINCI_SCRIPTS"] = str(scripts_home)
    sys.path.insert(0, str(scripts_home))

    load_dotenv()
    if args.dry_run or args.replay_dir or args.no_paid:
        os.environ["AISA_DRY_RUN"] = "1"

    skip_set = {s.strip() for s in args.skip.split(",") if s.strip()}
    if args.replay_dir or args.no_paid:
        skip_set.update({"video", "verify", "doable"})
    if args.replay_dir:
        # mock/skip live external collection; consume fixture files already in workdir/replay-dir
        skip_set.update({"track", "news", "higgsfield", "video", "verify", "doable"})
        print("[v2] OFFLINE REPLAY/FIXTURE mode; live network and paid AIsa calls are skipped (mocked by skip).")
    if args.legacy_only:
        skip_set.update({"track", "news", "higgsfield", "video", "verify", "doable"})
        print("[v2] LEGACY-ONLY: reuse already-captured scans; sources/daily stay skipped_budget/blocked_unbounded_cost unless a verified hard cost cap exists (not implemented); finders may use --skip trends only; then merge/push.")

    date_str = args.date
    slot = args.slot
    v2_run_dir = workdir / "v2_run"
    v2_run_dir.mkdir(parents=True, exist_ok=True)

    status_path = v2_run_dir / f"status-{date_str}-{slot}.json"
    summary_path = v2_run_dir / f"summary-{date_str}-{slot}.json"

    ledger = Ledger(path=str(workdir / "v2_spend.json"), date=date_str, hard_cap_usd=args.hard_cap, today_prior_usd=args.today_prior)

    steps_status = {}
    coverage = new_coverage()
    errors = []

    save_json(status_path, {"status": "start", "date": date_str, "slot": slot, "timestamp": bj_stamp()})

    compact_date = date_str.replace("-", "")
    if args.replay_dir:
        src = Path(args.replay_dir).resolve()
        if src != workdir:
            for pat in (f"tracks-{compact_date}-{slot}.json", f"news-{compact_date}.json",
                        f"meme-{compact_date}.json", f"higgsfield-{compact_date}.json",
                        f"xnew-{compact_date}-{slot}.json", f"xnew-{compact_date}.json",
                        "doable.json", "v2_spend.json"):
                fp = src / pat
                if fp.exists():
                    safe_copy(fp, workdir / pat)
        os.environ["XINCI_SCRIPTS"] = str(scripts_home)
    tracks_file = workdir / f"tracks-{compact_date}-{slot}.json"

    # X new finding path
    xnew_path = args.xnew
    if not xnew_path:
        for cand in (
            workdir / f"xnew-{compact_date}-{slot}.json",
            workdir / f"xnew-{compact_date}.json",
            v2_run_dir / f"xnew-{compact_date}-{slot}.json",
        ):
            if cand.exists():
                xnew_path = str(cand)
                break

    x_status = "ok" if xnew_path and Path(xnew_path).exists() else "missing"
    if args.require_x and x_status == "missing":
        save_json(status_path, {"status": "error", "reason": "require-x and xnew missing", "timestamp": bj_stamp()})
        sys.exit(3)

    # Step 2: Track scan
    if "track" not in skip_set:
        cmd = ["python3", "-u", "track_scan.py", "--mode", slot, "--date", date_str]
        if args.x_input:
            cmd.extend(["--x-input", args.x_input])
        res = run_cmd(cmd)
        steps_status["track"] = res
        if res["returncode"] != 0:
            errors.append("track_scan failed")
            _record_cov(coverage, "track", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)
            sys.exit(1)
    else:
        steps_status["track"] = {"skipped": True}
    _record_cov(coverage, "track", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)

    # Step 3: Classify games
    game_class_file = v2_run_dir / f"game-class-{date_str}.json"
    if tracks_file.exists():
        try:
            t_data = load_json(str(tracks_file))
            if isinstance(t_data, dict) and t_data.get("errors"):
                errors.extend([str(e) for e in t_data["errors"]])
            games = ((t_data.get("tracks") or {}).get("game") or {}).get("items") or []
            history = load_history(dir=workdir / "track_state" / "chart_snapshots")
            classed = classify_chart_items(games, history, date_str)
            write_game_snapshot(date_str, classed, Path(game_class_file))
            save_json(str(game_class_file), {"date": date_str, "items": classed,
                "is_first_discovery": [x for x in classed if x.get("is_first_discovery")],
                "new_on_chart": [x for x in classed if x.get("new_on_chart")],
                "reheating": [x for x in classed if x.get("reheating")],
                "still_popular": [x for x in classed if x.get("still_popular")]})
            steps_status["classify_games"] = {"status": "ok", "path": str(game_class_file)}
        except Exception as e:
            steps_status["classify_games"] = {"status": "error", "error": str(e)}
            errors.append(f"classify_games error: {e}")
    else:
        steps_status["classify_games"] = {"status": "missing_tracks"}

    # Step 4: news_scan.py
    if "news" not in skip_set:
        cmd = ["python3", "-u", "news_scan.py", "--date", date_str]
        res = run_cmd(cmd)
        steps_status["news"] = res
    else:
        steps_status["news"] = {"skipped": True}
    _record_cov(coverage, "news", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)

    # Step 5: higgsfield_scan.py
    if "higgsfield" not in skip_set:
        cmd = ["python3", "-u", "higgsfield_scan.py", "--date", date_str]
        res = run_cmd(cmd)
        steps_status["higgsfield"] = res
    else:
        steps_status["higgsfield"] = {"skipped": True}
    _record_cov(coverage, "higgsfield", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)

    # Step 6: aisa_video_scan.py
    if "video" not in skip_set:
        cmd = [
            "python3", "-u", "aisa_video_scan.py",
            "--date", date_str,
            "--ledger", str(workdir / "v2_spend.json"),
            "--hard-cap", str(args.hard_cap),
            "--today-prior", str(args.today_prior),
            "--out", str(workdir / f"meme-{compact_date}.json"),
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        res = run_cmd(cmd)
        steps_status["video"] = res
    else:
        steps_status["video"] = {"skipped": True}
    _record_cov(coverage, "video", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)

    # Step 7: Build priority list
    priority_path = v2_run_dir / f"priority-{date_str}.json"
    try:
        keywords = []
        if xnew_path and Path(xnew_path).exists():
            xn = load_json(xnew_path)
            if isinstance(xn, list):
                keywords.extend(xn)
            elif isinstance(xn, dict) and "keywords" in xn:
                keywords.extend(xn["keywords"])
        
        # Add a few is_new games if available
        if game_class_file.exists():
            g_cls = load_json(str(game_class_file))
            for item in g_cls.get("is_first_discovery", [])[:5]:
                if isinstance(item, dict) and "name" in item:
                    keywords.append(item["name"])
                elif isinstance(item, str):
                    keywords.append(item)

        # normalize to {phrase,source,names,evidence}
        normed = []
        seenp = set()
        def _add(phrase, source="", evidence="", names=None):
            p0 = (phrase or "").strip() if isinstance(phrase, str) else ""
            if not p0: return
            k = p0.lower()
            if k in seenp: return
            seenp.add(k)
            normed.append({"phrase": p0, "source": source, "names": names or [p0], "evidence": evidence or ""})
        for kw in keywords:
            if isinstance(kw, dict):
                _add(kw.get("keyword") or kw.get("phrase") or kw.get("name"), kw.get("source") or "", kw.get("reason") or kw.get("evidence") or "", kw.get("names"))
            elif isinstance(kw, str):
                _add(kw)
        # meme + higgsfield keywords
        meme_p = Path(str(workdir / f"meme-{compact_date}.json"))
        if meme_p.exists():
            md = load_json(str(meme_p))
            block = (md.get("tracks") or {}).get("meme") or md
            for kw in block.get("keywords") or []:
                _add(kw.get("keyword"), "热梗轨", kw.get("reason") or "", [kw.get("from") or kw.get("keyword")])
        hf_p = workdir / f"higgsfield-{compact_date}.json"
        if hf_p.exists():
            hd = load_json(str(hf_p))
            block = (hd.get("tracks") or {}).get("higgsfield") or hd
            for kw in block.get("keywords") or []:
                _add(kw.get("keyword"), "Higgsfield", kw.get("reason") or "", [kw.get("from") or kw.get("keyword")])
        unique_kw = normed[:args.max_priority]
        save_json(str(priority_path), unique_kw)
        steps_status["priority"] = {"status": "ok", "count": len(unique_kw)}
    except Exception as e:
        steps_status["priority"] = {"status": "error", "error": str(e)}
        save_json(priority_path, {"date": date_str, "keywords": []})

    # Step 8: verify_priority.py
    if "verify" not in skip_set:
        cmd = [
            "python3", "-u", "verify_priority.py",
            "--input", str(priority_path),
            "--date", date_str,
            "--ledger", str(workdir / "v2_spend.json"),
            "--hard-cap", str(args.hard_cap),
            "--today-prior", str(args.today_prior),
            "--max-terms", str(args.max_priority)
        ]
        res = run_cmd(cmd)
        steps_status["verify"] = res
    else:
        steps_status["verify"] = {"skipped": True}
    _record_cov(coverage, "verify", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)


    # Legacy original-scope: sources/daily default-blocked (no hard cost cap).
    rem_now = remaining_budget_usd(ledger)
    if should_run_legacy_radar():
        rec = run_legacy_sources(workdir, date_str, replay=bool(args.replay_dir), no_paid=bool(args.no_paid), remaining_usd=rem_now)
    else:
        rec = blocked_unbounded_legacy_radar()
    steps_status["legacy_sources"] = rec
    set_step(coverage, "legacy_sources", rec.get("status") or "failed", rec.get("reason") or "", {k: rec[k] for k in rec if k not in ("status", "reason")})

    if should_run_legacy_radar():
        rec = run_legacy_daily(workdir, date_str, replay=bool(args.replay_dir), no_paid=bool(args.no_paid), remaining_usd=rem_now)
    else:
        rec = blocked_unbounded_legacy_radar()
    steps_status["legacy_daily"] = rec
    set_step(coverage, "legacy_daily", rec.get("status") or "failed", rec.get("reason") or "", {k: rec[k] for k in rec if k not in ("status", "reason")})

    if "finders" not in skip_set:
        rec = run_finders(workdir, date_str, replay=bool(args.replay_dir), no_paid=bool(args.no_paid), remaining_usd=rem_now, quote_usd=None)
        steps_status["finders"] = rec
        set_step(coverage, "finders", rec.get("status") or "failed", rec.get("reason") or "", {k: rec[k] for k in rec if k not in ("status", "reason")})
    else:
        steps_status["finders"] = {"skipped": True}
        set_step(coverage, "finders", "skipped", "explicit --skip")

    # Step 9: doable
    doable_custom_out = v2_run_dir / f"doable-{date_str}.json"
    stale_doable = workdir / "doable.json"
    if "doable" not in skip_set:
        stub_path = v2_run_dir / f"report-stub-{date_str}.json"
        save_json(stub_path, {"date": date_str, "leads": [], "keywords": {}, "x": {"answered": 1}})
        
        # reload ledger so video/verify spend counts against remaining
        ledger = Ledger(path=str(workdir / "v2_spend.json"), date=date_str, hard_cap_usd=args.hard_cap, today_prior_usd=args.today_prior)
        rem = ledger.remaining_usd
        max_spend = min(0.20, rem if rem > 0 else 0.0)
        if rem <= 0.02:
            steps_status["doable"] = {"skipped": True, "reason": "budget remaining too low after video/verify"}
            skip_set.add("doable_budget")
        
        if "doable_budget" in skip_set:
            cmd = None
        else:
          cmd = [
            "python3", "-u", "doable.py",
            "--report", str(stub_path),
            "--extra-file", str(priority_path),
            "--out", str(v2_run_dir / f"doable-{date_str}.md"),
            "--only-extra",
            "--max-spend", str(max_spend)
        ]
        if cmd:
            res = run_cmd(cmd)
            steps_status["doable"] = res
        # Check if doable.py produced a json sidecar or if we can find doable.json
        candidate_json = v2_run_dir / f"doable-{date_str}.json"
        if candidate_json.exists():
            import shutil
            if candidate_json.resolve() != Path(doable_custom_out).resolve():
                shutil.copy(candidate_json, doable_custom_out)
            safe_copy(candidate_json, workdir / "doable.json")
        elif (workdir / "doable.json").exists() and (workdir / "doable.json").stat().st_mtime > time.time() - 300:
            safe_copy(workdir / "doable.json", doable_custom_out)
    else:
        steps_status["doable"] = {"skipped": True}
        if stale_doable.exists() and not args.replay_dir and not args.legacy_only:
            stale_dest = v2_run_dir / "doable-stale.json"
            import shutil
            if stale_doable.resolve() != stale_dest.resolve():
                shutil.move(stale_doable, stale_dest)
    _record_cov(coverage, "doable", steps_status, args=args, workdir=workdir, compact_date=compact_date, slot=slot, date_str=date_str)
    if steps_status.get("doable", {}).get("reason") and "budget" in steps_status["doable"].get("reason", "").lower():
        set_step(coverage, "doable", "skipped_budget", steps_status["doable"]["reason"])

    # Step 10: merge_board.py
    stub_path = v2_run_dir / f"report-stub-{date_str}.json"
    if not stub_path.exists():
        save_json(stub_path, {"date": date_str, "leads": [], "keywords": {}, "x": {"answered": 1}})
    report_for_merge = stub_path
    dated_report = v2_run_dir / f"report-{date_str}.json"
    # Never pass undated stale /workspace/xinci/report.json as today.
    if dated_report.exists():
        try:
            dd = load_json(str(dated_report))
            if isinstance(dd, dict) and str(dd.get("date") or "")[:10] == date_str:
                report_for_merge = dated_report
        except Exception:
            pass
    
    cmd = ["python3", "-u", "merge_board.py", "--date", date_str, "--report", str(report_for_merge)]
    res = run_cmd(cmd)
    steps_status["merge"] = res
    if res["returncode"] != 0:
        errors.append("merge_board failed")
        set_step(coverage, "merge", "failed", "merge_board failed")
    else:
        set_step(coverage, "merge", "ok", f"report={report_for_merge.name}", {"report": str(report_for_merge)})

    # Step 11: select quotas & push_board
    board_kw_path = workdir / "board_keywords.json"
    if board_kw_path.exists():
        try:
            bk = load_json(str(board_kw_path))
            filtered_bk = select_board_keywords(bk)
            save_json(str(board_kw_path), filtered_bk)
            steps_status["select_board_keywords"] = {"status": "ok"}
        except Exception as e:
            steps_status["select_board_keywords"] = {"status": "error", "error": str(e)}

    if "push" not in skip_set:
        push_cmd = ["python3", "-u", "push_board.py", "--date", date_str]
        if args.no_push or args.dry_run:
            push_cmd.append("--dry-run")
        res = run_cmd(push_cmd)
        steps_status["push"] = res
        if args.no_push or args.dry_run:
            set_step(coverage, "push", "ok" if res.get("returncode", 1) == 0 else "failed", "dry-run / no-push: payload written, board not upserted")
        elif res.get("returncode", 1) == 0:
            set_step(coverage, "push", "ok")
        else:
            set_step(coverage, "push", "failed", f"exit {res.get('returncode')}")
    else:
        steps_status["push"] = {"skipped": True}
        set_step(coverage, "push", "skipped", "explicit --skip")

    # Step 12: Summary
    cov_path = v2_run_dir / f"coverage-{date_str}-{slot}.json"
    save_json(str(cov_path), {"date": date_str, "slot": slot, "coverage": coverage, "written_at": bj_stamp()})
    summary_data = {
        "date": date_str,
        "slot": slot,
        "steps_status": steps_status,
        "coverage": coverage,
        "coverage_path": str(cov_path),
        "ledger": ledger.as_dict(),
        "x_status": x_status,
        "errors": errors
    }
    save_json(summary_path, summary_data)
    save_json(status_path, {"status": "completed", "timestamp": bj_stamp()})

    # Print short summary
    rem_usd = ledger.remaining_usd
    meme_count = 0 # Can inspect board keywords if present
    game_new_count = 0
    if game_class_file.exists():
        try:
            gc = load_json(str(game_class_file))
            game_new_count = len(gc.get("is_first_discovery", []))
        except:
            pass

    print(f"\n[v2 Workflow Summary]")
    print(f"Date: {date_str} | Slot: {slot}")
    print(f"Remaining USD: {rem_usd:.3f}")
    print(f"Game New Count: {game_new_count}")
    print(f"X Status: {x_status}")
    print(f"Errors: {len(errors)}")

    if res.get("returncode", 0) == 0 and "merge" in steps_status and steps_status["merge"].get("returncode", 0) == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
