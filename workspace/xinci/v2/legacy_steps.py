import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

STEP_NAMES = [
    "track",
    "news",
    "higgsfield",
    "video",
    "verify",
    "legacy_sources",
    "legacy_daily",
    "finders",
    "doable",
    "merge",
    "push",
]

ALLOWED_STATUSES = {"ok", "failed", "skipped_budget", "skipped_replay", "skipped", "cache_reuse"}

UNBOUNDED_COST_REASON = (
    "radar sources/daily 官方 CLI 无 --max-usd 硬费用上限（该旗仅用于 history）。"
    "2026-11-19 即使 skip 付费组仍发生 AIsa 数据扣费约 $0.243。"
    "默认不执行，记 skipped_budget/blocked_unbounded_cost。"
    "免费替代由现有 track/news/higgsfield 提供。"
    "可验证硬费用控制尚未实现，不得自称全部上游覆盖。"
)

def verified_hard_cost_control(control=None) -> bool:
    # 本次不实现上游硬费用控制；没有可验证硬上限对象时恒为 False。
    return False

def should_run_legacy_radar(hard_cost_control=None) -> bool:
    return verified_hard_cost_control(hard_cost_control)

def blocked_unbounded_legacy_radar() -> dict:
    return {
        "status": "skipped_budget",
        "block": "blocked_unbounded_cost",
        "reason": UNBOUNDED_COST_REASON,
    }


REPO_DIR = Path("/workspace/xinci/repo")
CONFIG_PATH = REPO_DIR / "config.json"
STATE_DIR = REPO_DIR / "state"
FINDERS_SCRIPT = Path("/workspace/xinci/finders.py")

SECRET_KEY_PATTERN = re.compile(
    r"(?:aisa|api[_-]?key|token|secret|password|bearer)[^a-zA-Z0-9]*([a-zA-Z0-9_\-\.]{10,})",
    re.IGNORECASE,
)

def redact_secrets(text: str) -> str:
    if not text:
        return ""
    # Redact sensitive patterns
    redacted = text
    for match in SECRET_KEY_PATTERN.finditer(text):
        secret = match.group(1)
        if secret and len(secret) > 4:
            masked = secret[:2] + "****" + secret[-2:]
            redacted = redacted.replace(secret, masked)
    
    # Also catch env variables or common patterns if they leaked
    aisa_key = os.environ.get("AISA_API_KEY")
    if aisa_key and len(aisa_key) > 4:
        redacted = redacted.replace(aisa_key, aisa_key[:2] + "****" + aisa_key[-2:])
    return redacted

def new_coverage() -> Dict[str, Dict[str, str]]:
    return {name: {"status": "pending"} for name in STEP_NAMES}

def set_step(coverage: Dict[str, Dict[str, Any]], name: str, status: str, reason: str = "", extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {ALLOWED_STATUSES}")
    if name not in coverage:
        coverage[name] = {}
    
    record = coverage[name]
    record["status"] = status
    if reason:
        record["reason"] = reason
    if extra:
        record.update(extra)
    return record

def remaining_budget_usd(ledger: Any) -> float:
    if ledger is not None and hasattr(ledger, "remaining_usd"):
        try:
            return float(ledger.remaining_usd)
        except (TypeError, ValueError):
            pass
    return 0.0

def _tail_output(text: str, max_lines: int = 30) -> str:
    if not text:
        return ""
    lines = text.strip().splitlines()
    if len(lines) <= max_lines:
        return redact_secrets("\n".join(lines))
    return redact_secrets("\n".join(lines[-max_lines:]))

def run_legacy_sources(workdir: Path, date_str: str, *, replay: bool = False, no_paid: bool = False, remaining_usd: Optional[float] = None) -> dict:
    if not should_run_legacy_radar():
        return blocked_unbounded_legacy_radar()
    if replay:
        return {"status": "skipped_replay", "reason": "replay mode enabled; legacy sources not executed."}
    if no_paid:
        return {"status": "skipped", "reason": "no_paid mode enabled; legacy sources not executed."}

    v2_run_dir = workdir / "v2_run"
    v2_run_dir.mkdir(parents=True, exist_ok=True)
    out_path = v2_run_dir / f"sources-{date_str}.md"

    # Command: python3 -m radar sources --config CONFIG --state STATE --skip x --out OUT
    skip_args = "x"
    cmd = [
        sys.executable,
        "-m",
        "radar",
        "sources",
        "--config",
        str(CONFIG_PATH),
        "--state",
        str(STATE_DIR),
        "--skip",
        skip_args,
        "--out",
        str(out_path),
    ]

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    repo_path_str = str(REPO_DIR)
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{repo_path_str}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = repo_path_str

    try:
        res = subprocess.run(
            cmd,
            cwd=str(REPO_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if res.returncode == 0:
            return {
                "status": "ok",
                "reason": "Skipped paid slice x (AIsa X); ran Hugging Face and free legacy sources successfully.",
                "out": str(out_path),
            }
        else:
            err_text = _tail_output(res.stderr or res.stdout)
            return {
                "status": "failed",
                "reason": f"radar sources exited with code {res.returncode}. Tail: {err_text}",
            }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "reason": "radar sources timed out after 180s."}
    except Exception as e:
        return {"status": "failed", "reason": f"Exception running radar sources: {redact_secrets(str(e))}"}

def run_legacy_daily(workdir: Path, date_str: str, *, replay: bool = False, no_paid: bool = False, remaining_usd: Optional[float] = None) -> dict:
    if not should_run_legacy_radar():
        return blocked_unbounded_legacy_radar()
    if replay:
        return {"status": "skipped_replay", "reason": "replay mode enabled; legacy daily not executed."}
    if no_paid:
        return {"status": "skipped", "reason": "no_paid mode enabled; legacy daily not executed."}

    v2_run_dir = workdir / "v2_run"
    v2_run_dir.mkdir(parents=True, exist_ok=True)
    out_path = v2_run_dir / f"report-{date_str}.md"

    # Skip list for daily to avoid uncontrollable paid/uncontrollable slices:
    skip_list = "x,review,usecases,judge,newsites,asks,sellers,builders,money,revenue,feeds,tutorials,sidelights"

    cmd = [
        sys.executable,
        "-m",
        "radar",
        "daily",
        "--config",
        str(CONFIG_PATH),
        "--state",
        str(STATE_DIR),
        "--skip",
        skip_list,
        "--out",
        str(out_path),
    ]

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    repo_path_str = str(REPO_DIR)
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{repo_path_str}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = repo_path_str

    try:
        res = subprocess.run(
            cmd,
            cwd=str(REPO_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if res.returncode == 0:
            # daily also writes sibling .json
            json_path = out_path.with_suffix(".json")
            # official daily sidecar may omit date; stamp it so merge will not treat a dated today file as undated
            if json_path.exists():
                try:
                    payload = json.loads(json_path.read_text())
                    if isinstance(payload, dict):
                        payload.setdefault("date", date_str)
                        payload.setdefault("generated_at", date_str)
                        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
                except Exception:
                    pass
            return {
                "status": "ok",
                "reason": f"Ran free signals successfully; skipped paid/uncontrollable slices: {skip_list}",
                "out": str(out_path),
                "json_out": str(json_path),
            }
        else:
            err_text = _tail_output(res.stderr or res.stdout)
            return {
                "status": "failed",
                "reason": f"radar daily exited with code {res.returncode}. Tail: {err_text}",
            }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "reason": "radar daily timed out after 600s."}
    except Exception as e:
        return {"status": "failed", "reason": f"Exception running radar daily: {redact_secrets(str(e))}"}

def run_finders(workdir: Path, date_str: str, *, replay: bool = False, no_paid: bool = False, remaining_usd: Optional[float] = None, quote_usd: Optional[float] = None) -> dict:
    if replay:
        return {"status": "skipped_replay", "reason": "replay mode enabled; finders not executed."}
    if no_paid:
        return {"status": "skipped", "reason": "no_paid mode enabled; finders not executed."}

    # 仅保留已验证零费分支：强制 --skip trends（报价 may_exceed，CLI 无硬上限，不得跑 trends）。
    skip_trends = True
    reason_msg = "finders 仅保留已验证零费分支 --skip trends（ac/appstore/hn）；trends 无硬费用上限且报价 may_exceed，默认不跑"

    cmd = [
        sys.executable,
        str(FINDERS_SCRIPT),
        "--date",
        date_str,
    ]
    if skip_trends:
        cmd.extend(["--skip", "trends"])

    env = os.environ.copy()
    env["XINCI_HOME"] = str(workdir)

    pythonpath_parts = ["/workspace/xinci", str(REPO_DIR)]
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = ":".join(pythonpath_parts)

    try:
        res = subprocess.run(
            cmd,
            cwd=str(workdir) if workdir.exists() else "/workspace/xinci",
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if res.returncode == 0:
            rec = {"status": "ok", "reason": reason_msg}
            if skip_trends:
                rec["trends"] = "skipped_budget"
            return rec
        else:
            err_text = _tail_output(res.stderr or res.stdout)
            return {
                "status": "failed",
                "reason": f"finders script exited with code {res.returncode}. Tail: {err_text}",
            }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "reason": "finders script timed out after 300s."}
    except Exception as e:
        return {"status": "failed", "reason": f"Exception running finders: {redact_secrets(str(e))}"}
