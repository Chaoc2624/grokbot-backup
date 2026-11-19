import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path("/workspace/xinci")
sys.path.insert(0, str(ROOT))

from v2.metrics import parse_semrush_overview_csv, parse_missing_as_nodata, 立项_status
from v2.select_keywords import select_board_keywords, filter_derived, primary_source
from v2.extract_video import extract_video_keywords, is_generic_video_phrase
from run_v2 import safe_copy


CSV = "Keyword;Search Volume;CPC;Competition;Number of Results\r\ngpts;5400;0.14;0.24;122\r\nzeroed;0;0.01;0.1;10\r\n"


class TestSemrushParseShapes(unittest.TestCase):
    def test_csv_zero_vs_missing(self):
        parsed = parse_semrush_overview_csv(CSV)
        self.assertEqual(parsed["gpts"]["volume"], 5400)
        self.assertFalse(parsed["gpts"]["nodata"])
        self.assertEqual(parsed["zeroed"]["volume"], 0)
        self.assertFalse(parsed["zeroed"]["nodata"])
        miss = parse_missing_as_nodata(["gpts", "absent", "zeroed"], parsed)
        self.assertTrue(miss["absent"]["nodata"])
        self.assertIsNone(miss["absent"]["volume"])

    def test_dict_wrapper_with_csv(self):
        parsed = parse_semrush_overview_csv({"output": CSV, "successful": True})
        self.assertEqual(parsed["gpts"]["volume"], 5400)

    def test_dict_error_and_empty(self):
        self.assertEqual(parse_semrush_overview_csv({"error": "no coverage", "successful": False}), {})
        self.assertEqual(parse_semrush_overview_csv(""), {})
        self.assertEqual(parse_semrush_overview_csv(None), {})
        self.assertEqual(parse_semrush_overview_csv([]), {})

    def test_立项_null_not_zero(self):
        st = 立项_status(None, None, None, True)
        self.assertFalse(st["passed_立项"])
        self.assertEqual(st["status"], "待验证")


class TestSelectQuality(unittest.TestCase):
    def test_drops_seeds_derived_ai_and_evergreen(self):
        entries = [
            {"phrase": "CapCut Peek AI", "source": "热梗轨", "evidence": "type peek", "names": ["CapCut Peek AI"]},
            {"phrase": "CapCut AI template", "source": "热梗轨", "evidence": "seed", "from": "seed"},
            {"phrase": "AI photo to video", "source": "热梗轨", "evidence": "seed"},
            {"phrase": "Counter-Strike 2", "source": "游戏轨", "evidence": "Steam 畅销"},
            {"phrase": "Dota 2", "source": "游戏轨", "evidence": "Steam 畅销"},
            {"phrase": "AION 2", "source": "游戏轨", "evidence": "Steam 畅销：AION 2", "names": ["AION 2"]},
            {"phrase": "+1 Heart Per Kill", "source": "游戏轨", "evidence": "Roblox · Up-and-Coming", "names": ["+1 Heart Per Kill"]},
            {"phrase": "Qwen4-Max", "source": "书签X/AI工具轨", "evidence": "官方首发", "names": ["Qwen4-Max"]},
            {"phrase": "Qwen4-Max ai", "source": "AI工具轨", "evidence": "derived", "names": ["Qwen4-Max ai"]},
            {"phrase": "Room AI", "source": "AI工具轨", "evidence": "product hunt", "names": ["Room AI"]},
            {"phrase": "Gemini 4 Neon", "source": "书签X", "evidence": "官方发布", "names": ["Gemini 4 Neon"]},
        ]
        res = select_board_keywords(entries)
        phrases = [e["phrase"] for e in res]
        self.assertIn("CapCut Peek AI", phrases)
        self.assertNotIn("CapCut AI template", phrases)
        self.assertNotIn("AI photo to video", phrases)
        self.assertNotIn("Counter-Strike 2", phrases)
        self.assertNotIn("Dota 2", phrases)
        self.assertNotIn("Qwen4-Max ai", phrases)
        self.assertIn("Qwen4-Max", phrases)
        self.assertIn("Room AI", phrases)
        self.assertIn("AION 2", phrases)
        self.assertLessEqual(len(res), 40)
        self.assertEqual(sum(1 for e in res if primary_source(e.get("source")) == "游戏轨"), 2)

    def test_does_not_pad_below_cap(self):
        res = select_board_keywords([
            {"phrase": "AION 2", "source": "游戏轨", "evidence": "chart", "names": ["AION 2"]},
            {"phrase": "CapCut Peek AI", "source": "热梗轨", "evidence": "peek", "names": ["CapCut Peek AI"]},
        ])
        self.assertEqual(len(res), 2)

    def test_video_zero_ok_without_seeds(self):
        res = select_board_keywords([
            {"phrase": "CapCut AI template", "source": "热梗轨", "evidence": "anchor", "from": "seed"},
            {"phrase": "Foo", "source": "AI工具轨", "evidence": "ok", "names": ["Foo"]},
        ])
        self.assertEqual([e["phrase"] for e in res], ["Foo"])


class TestExtractVideo(unittest.TestCase):
    def test_named_plays_not_generic_caption(self):
        items = [
            {"name": "This viral PEEK trend is everywhere, so I had to try it! 👀✨", "url": "https://www.instagram.com/reel/Df2JChERXMF/", "platform": "instagram"},
            {"name": "Try it on CapCut — go to AI Lab and search “Rich” 👀", "url": "https://www.instagram.com/reel/DfvBPoggoAn/", "platform": "instagram"},
            {"name": "Turn any photo into a viral AI video with CapCut! 🤩💗", "url": "https://www.instagram.com/reel/Df2ndHkg8Es/", "platform": "instagram", "desc": "发现阶段，未做画面核验不得称独立成片"},
            {"name": "Create the Viral Sheru Bhai Trend with AI! 🤯🔥", "url": "https://www.instagram.com/reel/DftmKBkx2nt/", "platform": "instagram"},
        ]
        out = extract_video_keywords(items)
        kws = [k["keyword"] for k in out["keywords"]]
        self.assertIn("CapCut Peek AI", kws)
        self.assertTrue(any("Rich" in k or "rich" in k.lower() for k in kws))
        self.assertTrue(any("Sheru" in k for k in kws))
        self.assertFalse(any("pool" in k.lower() for k in kws))
        self.assertFalse(is_generic_video_phrase("CapCut Peek AI"))
        self.assertTrue(is_generic_video_phrase("CapCut AI template"))


class TestSafeCopyAndOnlyExtra(unittest.TestCase):
    def test_safe_copy_same_file_ok(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "a.json"
            f.write_text("{}")
            self.assertFalse(safe_copy(f, f))
            dest = Path(td) / "b.json"
            self.assertTrue(safe_copy(f, dest))
            self.assertEqual(dest.read_text(), "{}")

    def test_doable_only_extra_skips_xnew_glob(self):
        import doable
        with tempfile.TemporaryDirectory() as td:
            here = Path(td)
            (here / "xnew-20261119-pm.json").write_text(json.dumps({
                "items": [{"name": "ShouldNotAppear", "keyword": "ShouldNotAppear", "kind": "model", "reason": "x"}]
            }), encoding="utf-8")
            old = doable.HERE
            try:
                doable.HERE = here
                extra = [{"phrase": "OnlyExtraTerm", "source": "手动", "names": ["OnlyExtraTerm"], "evidence": "t"}]
                out = []
                terms = doable.collect({"leads": [], "keywords": {}}, extra, 20, "2026-11-19", out, only_extra=True)
            finally:
                doable.HERE = old
        phrases = [t.get("phrase") for t in terms]
        self.assertIn("onlyextraterm", phrases)
        self.assertNotIn("shouldnotappear", phrases)


class TestRunV2OfflineReplay(unittest.TestCase):
    def test_run_v2_replay_exits_zero_and_payload_compliant(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            date, slot, compact = "2026-11-19", "pm", "20261119"
            meme_kw = extract_video_keywords([
                {"name": "This viral PEEK trend is everywhere", "url": "https://example.com/peek", "platform": "instagram", "first_seen": "2026-11-19 16:59"},
                {"name": "Type ‘Rich’ in the AI Lab", "url": "https://example.com/rich", "platform": "instagram"},
            ])["keywords"]
            # include seeds that must not reach the board 40
            meme_kw_bad = [
                {"keyword": "CapCut AI template", "reason": "seed", "from": "seed"},
                {"keyword": "AI photo to video", "reason": "seed", "from": "seed"},
            ]
            (td / f"meme-{compact}.json").write_text(json.dumps({
                "tracks": {"meme": {"items": [
                    {"name": "This viral PEEK trend is everywhere", "url": "https://example.com/peek", "source": "热梗轨", "desc": "发现阶段，未做画面核验不得称独立成片"}
                ], "keywords": meme_kw + meme_kw_bad}},
                "notes": "fixture; external APIs mocked/skipped"
            }, ensure_ascii=False, indent=1), encoding="utf-8")
            (td / f"tracks-{compact}-{slot}.json").write_text(json.dumps({
                "tracks": {
                    "game": {"items": [
                        {"name": "Counter-Strike 2", "source": "Steam 畅销", "url": "https://store.steampowered.com/app/730", "is_new": False, "platform": "steam", "desc": "Steam 畅销：Counter-Strike 2"},
                        {"name": "AION 2", "source": "Steam 畅销", "url": "https://store.steampowered.com/search/?term=AION%202", "is_new": False, "platform": "steam", "desc": "Steam 畅销：AION 2"},
                        {"name": "+1 Heart Per Kill", "source": "Roblox · Up-and-Coming", "url": "https://www.roblox.com/games/82331798712738", "is_new": False, "platform": "roblox", "desc": "Roblox Up-and-Coming"},
                    ], "keywords": [
                        {"keyword": "Counter-Strike 2", "reason": "Steam 畅销"},
                        {"keyword": "AION 2", "reason": "Steam 畅销：AION 2"},
                        {"keyword": "+1 Heart Per Kill", "reason": "Roblox · Up-and-Coming"},
                        {"keyword": "AION 2 unblocked", "reason": "derived"},
                    ]},
                    "ai_tools": {"items": [
                        {"name": "Room AI", "source": "Product Hunt", "url": "https://example.com/room", "desc": "PH listing"}
                    ], "keywords": [
                        {"keyword": "Room AI", "reason": "PH"},
                        {"keyword": "Room AI ai", "reason": "derived"},
                    ]}
                }
            }, ensure_ascii=False, indent=1), encoding="utf-8")
            (td / f"news-{compact}.json").write_text(json.dumps({
                "label": "2026-11-19 新闻轨", "tracks": {"news": {"items": [{"name": "Nutcake", "url": "https://example.com/n", "source": "新闻轨", "desc": "news"}], "keywords": [{"keyword": "Nutcake", "reason": "rss"}]}}
            }, ensure_ascii=False), encoding="utf-8")
            (td / f"higgsfield-{compact}.json").write_text(json.dumps({
                "date": date, "first_run": True, "status": "zero_new",
                "coverage": {"effects": {"now_count": 1, "new_count": 0, "first_run": True}},
                "tracks": {"higgsfield": {"items": [], "keywords": []}}
            }, ensure_ascii=False), encoding="utf-8")
            (td / f"xnew-{compact}-{slot}.json").write_text(json.dumps({
                "label": "20261119-pm", "empty": False,
                "items": [{"name": "Gemini 4 Neon", "keyword": "Gemini 4 Neon", "source": "@GoogleDeepMind", "url": "https://x.com/GoogleDeepMind/status/2123167884411077030", "reason": "官方发布", "desc": "Gemini 4 Neon 正在推出", "kind": "model", "first_seen": "2026-11-19 05:34"}],
                "keywords": [{"keyword": "Gemini 4 Neon", "reason": "官方发布"}]
            }, ensure_ascii=False, indent=1), encoding="utf-8")
            (td / "v2_run").mkdir()
            env = os.environ.copy()
            env["XINCI_HOME"] = str(td)
            env["XINCI_SCRIPTS"] = str(ROOT)
            env["AISA_DRY_RUN"] = "1"
            env["PYTHONPATH"] = str(ROOT)
            cmd = [
                sys.executable, "-u", str(ROOT / "run_v2.py"),
                "--date", date, "--slot", slot,
                "--replay-dir", str(td),
                "--workdir", str(td),
                "--no-paid", "--no-push",
                "--today-prior", "0",
                "--xnew", str(td / f"xnew-{compact}-{slot}.json"),
            ]
            proc = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(proc.returncode, 0, proc.stdout[-2000:] + "\n" + proc.stderr[-2000:])
            payload_path = td / "board_payload.json"
            self.assertTrue(payload_path.exists(), proc.stdout[-1500:])
            payload = json.loads(payload_path.read_text())
            self.assertEqual(payload.get("label"), "2026-11-19 新词雷达")
            self.assertIn("items", payload)
            self.assertIn("keywords", payload)
            kws = [k["keyword"] if isinstance(k, dict) else k for k in payload["keywords"]]
            self.assertNotIn("CapCut AI template", kws)
            self.assertNotIn("AI photo to video", kws)
            self.assertNotIn("Counter-Strike 2", kws)
            self.assertNotIn("Room AI ai", kws)
            self.assertLessEqual(len(kws), 40)
            self.assertIn("OFFLINE REPLAY/FIXTURE", proc.stdout)
            status = json.loads((td / "v2_run" / f"status-{date}-{slot}.json").read_text())
            self.assertEqual(status.get("status"), "completed")
            cov_path = td / "v2_run" / f"coverage-{date}-{slot}.json"
            self.assertTrue(cov_path.exists(), "coverage file missing")
            cov = json.loads(cov_path.read_text()).get("coverage") or {}
            for name in ("track","news","higgsfield","video","verify","legacy_sources","legacy_daily","finders","doable","merge","push"):
                self.assertIn(name, cov, name)
                self.assertIn(cov[name].get("status"), ("ok","failed","skipped_budget","skipped_replay","skipped","cache_reuse"))
                self.assertNotEqual(cov[name].get("status"), "pending")
            for name in ("legacy_sources","legacy_daily"):
                self.assertEqual(cov[name].get("status"), "skipped_budget", cov[name])
                self.assertEqual(cov[name].get("block"), "blocked_unbounded_cost", cov[name])
            self.assertEqual(cov["finders"].get("status"), "skipped_replay", cov["finders"])

class TestLegacyScheduling(unittest.TestCase):
    def test_replay_and_no_paid_are_explicit(self):
        from v2.legacy_steps import run_legacy_sources, run_legacy_daily, run_finders, new_coverage, set_step, STEP_NAMES
        from pathlib import Path
        rec = run_legacy_sources(Path("/tmp"), "2026-11-19", replay=True)
        self.assertEqual(rec["status"], "skipped_budget")
        self.assertEqual(rec.get("block"), "blocked_unbounded_cost")
        rec = run_legacy_daily(Path("/tmp"), "2026-11-19", no_paid=True)
        self.assertEqual(rec["status"], "skipped_budget")
        self.assertEqual(rec.get("block"), "blocked_unbounded_cost")
        rec = run_finders(Path("/tmp"), "2026-11-19", replay=True, quote_usd=None)
        self.assertEqual(rec["status"], "skipped_replay")
        cov = new_coverage()
        self.assertEqual(list(cov), STEP_NAMES)
        set_step(cov, "finders", "skipped_budget", "no quote cap")
        self.assertEqual(cov["finders"]["status"], "skipped_budget")
        self.assertIn("quote", cov["finders"]["reason"])


class TestLegacySafetyGate(unittest.TestCase):
    def test_should_run_legacy_radar_is_false(self):
        from v2.legacy_steps import should_run_legacy_radar, verified_hard_cost_control, blocked_unbounded_legacy_radar
        self.assertFalse(verified_hard_cost_control())
        self.assertFalse(should_run_legacy_radar())
        self.assertFalse(should_run_legacy_radar(hard_cost_control={"claimed": True}))
        blocked = blocked_unbounded_legacy_radar()
        self.assertEqual(blocked.get("status"), "skipped_budget")
        self.assertEqual(blocked.get("block"), "blocked_unbounded_cost")
        self.assertIn("max-usd", blocked.get("reason", ""))

    def test_run_legacy_radar_helpers_do_not_spawn(self):
        from unittest.mock import patch
        from pathlib import Path
        import v2.legacy_steps as ls

        def boom(*args, **kwargs):
            raise AssertionError("subprocess must not be called for unbounded legacy radar")

        with patch.object(ls.subprocess, "run", side_effect=boom), patch.object(ls.subprocess, "Popen", side_effect=boom):
            rec_src = ls.run_legacy_sources(Path("/tmp"), "2026-11-19", replay=False, no_paid=False)
            rec_day = ls.run_legacy_daily(Path("/tmp"), "2026-11-19", replay=False, no_paid=False)
        self.assertEqual(rec_src.get("status"), "skipped_budget")
        self.assertEqual(rec_src.get("block"), "blocked_unbounded_cost")
        self.assertEqual(rec_day.get("status"), "skipped_budget")
        self.assertEqual(rec_day.get("block"), "blocked_unbounded_cost")

    def test_finders_argv_always_skips_trends(self):
        from unittest.mock import patch
        from pathlib import Path
        import subprocess as real_sub
        import v2.legacy_steps as ls

        captured = []

        def fake_run(cmd, *args, **kwargs):
            captured.append(list(cmd))
            return real_sub.CompletedProcess(cmd, 0, "", "")

        with patch.object(ls.subprocess, "run", side_effect=fake_run):
            rec = ls.run_finders(
                Path("/tmp"), "2026-11-19",
                replay=False, no_paid=False, quote_usd=0.01, remaining_usd=1.0,
            )
        self.assertEqual(rec.get("status"), "ok")
        self.assertEqual(rec.get("trends"), "skipped_budget")
        self.assertTrue(captured, "finders command was not captured")
        argv = [str(x) for x in captured[0]]
        self.assertIn("--skip", argv)
        self.assertIn("trends", argv)
        self.assertNotIn("python -m radar", " ".join(argv))

    def test_default_run_v2_does_not_invoke_radar_sources_or_daily(self):
        """In-process default-style entry: never spawn `python -m radar sources/daily`."""
        from unittest.mock import patch
        from pathlib import Path
        import run_v2
        import v2.legacy_steps as ls

        date, slot, compact = "2026-11-19", "pm", "20261119"
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            meme_kw = extract_video_keywords([
                {"name": "This viral PEEK trend is everywhere", "url": "https://example.com/peek", "platform": "instagram"},
            ])["keywords"]
            (td / f"meme-{compact}.json").write_text(json.dumps({
                "tracks": {"meme": {"items": [], "keywords": meme_kw}}
            }, ensure_ascii=False), encoding="utf-8")
            (td / f"tracks-{compact}-{slot}.json").write_text(json.dumps({
                "tracks": {"game": {"items": [], "keywords": []}, "ai_tools": {"items": [], "keywords": []}}
            }, ensure_ascii=False), encoding="utf-8")
            (td / f"news-{compact}.json").write_text(json.dumps({
                "label": "2026-11-19 新闻轨", "tracks": {"news": {"items": [], "keywords": []}}
            }, ensure_ascii=False), encoding="utf-8")
            (td / f"higgsfield-{compact}.json").write_text(json.dumps({
                "date": date, "first_run": True, "tracks": {"higgsfield": {"items": [], "keywords": []}}
            }, ensure_ascii=False), encoding="utf-8")
            (td / f"xnew-{compact}-{slot}.json").write_text(json.dumps({
                "label": "20261119-pm", "empty": False,
                "items": [{"name": "Gemini 4 Neon", "keyword": "Gemini 4 Neon", "source": "@GoogleDeepMind", "url": "https://x.com/example/1"}],
                "keywords": [{"keyword": "Gemini 4 Neon", "reason": "官方发布"}]
            }, ensure_ascii=False), encoding="utf-8")
            (td / "v2_run").mkdir()

            seen_radar = []

            def _guard(cmd, *args, **kwargs):
                argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
                joined = " ".join(str(c) for c in argv)
                if ("-m" in [str(c) for c in argv] or " -m " in joined) and "radar" in joined and (
                    "sources" in joined or " daily" in joined or joined.endswith("daily") or " daily " in f" {joined} "
                ):
                    seen_radar.append(joined)
                    raise AssertionError(f"unbounded legacy radar invoked: {joined}")
                return orig_popen(cmd, *args, **kwargs)

            orig_popen = run_v2.subprocess.Popen
            orig_ls_run = ls.subprocess.run

            def ls_run_guard(cmd, *args, **kwargs):
                argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
                joined = " ".join(str(c) for c in argv)
                if "radar" in joined and ("sources" in joined or "daily" in joined):
                    seen_radar.append(joined)
                    raise AssertionError(f"unbounded legacy radar invoked: {joined}")
                return orig_ls_run(cmd, *args, **kwargs)

            argv = [
                str(ROOT / "run_v2.py"),
                "--date", date, "--slot", slot,
                "--replay-dir", str(td),
                "--workdir", str(td),
                "--no-paid", "--no-push",
                "--today-prior", "0",
                "--xnew", str(td / f"xnew-{compact}-{slot}.json"),
            ]
            env_home = os.environ.get("XINCI_HOME")
            os.environ["XINCI_HOME"] = str(td)
            os.environ["XINCI_SCRIPTS"] = str(ROOT)
            os.environ["AISA_DRY_RUN"] = "1"
            try:
                with patch.object(sys, "argv", argv), \
                     patch.object(run_v2.subprocess, "Popen", side_effect=_guard), \
                     patch.object(ls.subprocess, "run", side_effect=ls_run_guard):
                    with self.assertRaises(SystemExit) as cm:
                        run_v2.main()
                self.assertEqual(cm.exception.code, 0)
            finally:
                if env_home is None:
                    os.environ.pop("XINCI_HOME", None)
                else:
                    os.environ["XINCI_HOME"] = env_home

            self.assertEqual(seen_radar, [], f"radar was spawned: {seen_radar}")
            cov_path = td / "v2_run" / f"coverage-{date}-{slot}.json"
            self.assertTrue(cov_path.exists(), "coverage file missing")
            cov = json.loads(cov_path.read_text()).get("coverage") or {}
            for name in ("legacy_sources", "legacy_daily"):
                self.assertEqual(cov[name].get("status"), "skipped_budget", cov[name])
                self.assertEqual(cov[name].get("block"), "blocked_unbounded_cost", cov[name])
            self.assertNotEqual(cov.get("legacy_sources", {}).get("status"), "ok")
            self.assertNotEqual(cov.get("legacy_daily", {}).get("status"), "ok")



if __name__ == "__main__":
    unittest.main()
