#!/usr/bin/env python3
"""TG 群总结 via free-llm (almost zero Grok Bot tokens).

  python3 /workspace/tg/tg_free_digest.py --window last3h
  python3 /workspace/tg/tg_free_digest.py --window last3h --push
  python3 /workspace/tg/tg_free_digest.py --date 2026-10-26 --window 18-19 --skip-fetch
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DIGESTS = BASE / "digests"
GROUPS = BASE / "groups.json"
FREE_LLM = Path("/home/box/.local/bin/free-llm")
VENV_PY = BASE / "venv" / "bin" / "python"
PY = str(VENV_PY if VENV_PY.exists() else sys.executable)
TZ = timezone(timedelta(hours=8))

SYSTEM = """你是 TG 群总结写手。铁律：
1. 只写群成员实际说了什么。不加判断/警告/建议/评价/标签。
2. 禁止「别碰」「别学」「违规」「欺诈」「有风险」「不推荐」「注意」「建议」「待验证」「和你」。
3. 发言行必须原文：`> 发言人：原话 {{YYYY-MM-DD HH:MM:SS}}`；同一人连续用 ` · `；可用…截短。
4. content 格式：
### 话题名 (N 条 / M 人)
> 发言人：原话 {{…}}
### 零星消息
> 发言人：原话 {{…}}
5. 关注 eSIM/SIM/外卡/美卡/办电/保号/银行卡/开户/U卡/数字银行/VPS/家宽/羊毛。闲聊/成人/政治不收。
6. 无实质内容则 content 为「无重要内容」。
7. 只输出合法 JSON 对象，不要 markdown 围栏。不要网上核验段。
"""


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(BASE), text=True, capture_output=True)


def load_groups() -> list[dict]:
    return json.loads(GROUPS.read_text(encoding="utf-8"))


def resolve_window_meta(window: str, date: str | None):
    now = datetime.now(TZ)
    day = datetime.strptime(date, "%Y-%m-%d").date() if date else now.date()

    if window == "last3h":
        block = (now.hour // 3) * 3
        end = now.replace(minute=0, second=0, microsecond=0, hour=block)
        start = end - timedelta(hours=3)
        label = f"{start.hour:02d}-{24 if (end.date() > start.date() and end.hour == 0) else end.hour:02d}"
        path = DATA / start.strftime("%Y-%m-%d") / f"{label}.json"
        win_end = (
            f"{start.strftime('%Y-%m-%d')} 24:00"
            if (end.date() > start.date() and end.hour == 0)
            else end.strftime("%Y-%m-%d %H:%M")
        )
        return start.strftime("%Y-%m-%d"), label, False, start.strftime("%Y-%m-%d %H:%M"), win_end, path

    if window == "lasthour":
        end = now.replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=1)
        label = f"{start.hour:02d}-{(start.hour + 1) if start.hour < 23 else 24:02d}"
        path = DATA / start.strftime("%Y-%m-%d") / "hourly" / f"{start.hour:02d}.json"
        return (
            start.strftime("%Y-%m-%d"),
            label,
            False,
            start.strftime("%Y-%m-%d %H:%M"),
            end.strftime("%Y-%m-%d %H:%M"),
            path,
        )

    if window == "current":
        block = (now.hour // 3) * 3
        start = now.replace(minute=0, second=0, microsecond=0, hour=block)
        end = start + timedelta(hours=3)
        label = f"{start.hour:02d}-{24 if (end.date() > start.date() and end.hour == 0) else end.hour:02d}"
        path = DATA / start.strftime("%Y-%m-%d") / f"{label}.json"
        return (
            start.strftime("%Y-%m-%d"),
            label,
            True,
            start.strftime("%Y-%m-%d %H:%M"),
            now.strftime("%Y-%m-%d %H:%M"),
            path,
        )

    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", window)
    if not m:
        raise SystemExit(f"unsupported --window {window}")
    h1, h2 = int(m.group(1)), int(m.group(2))
    start = datetime(day.year, day.month, day.day, h1, 0, tzinfo=TZ)
    if h2 == 24:
        end = datetime(day.year, day.month, day.day, 0, 0, tzinfo=TZ) + timedelta(days=1)
    else:
        end = datetime(day.year, day.month, day.day, h2, 0, tzinfo=TZ)
    label = f"{h1:02d}-{h2:02d}"
    span = (h2 - h1) if h2 > h1 else (24 - h1 + h2)
    if span == 1:
        path = DATA / day.strftime("%Y-%m-%d") / "hourly" / f"{h1:02d}.json"
    else:
        path = DATA / day.strftime("%Y-%m-%d") / f"{label}.json"
    win_end = f"{day} 24:00" if h2 == 24 else end.strftime("%Y-%m-%d %H:%M")
    return day.strftime("%Y-%m-%d"), label, False, start.strftime("%Y-%m-%d %H:%M"), win_end, path


def fetch(window: str, date: str | None) -> Path:
    cmd = [PY, str(BASE / "tg_fetch.py"), "--window", window]
    if date and window not in ("last3h", "lasthour", "current"):
        cmd.extend(["--date", date])
    print(f"[tg_free_digest] fetch: {' '.join(cmd)}", file=sys.stderr)
    r = run(cmd)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout or "")
        raise SystemExit(f"tg_fetch failed rc={r.returncode}")
    _, _, _, _, _, path = resolve_window_meta(window, date)
    if not path.exists():
        for line in (r.stdout or "").splitlines()[::-1]:
            m = re.search(r"(/workspace/tg/data/\S+\.json)", line)
            if m and Path(m.group(1)).exists():
                return Path(m.group(1))
            s = line.strip()
            cand = Path(s) if s.startswith("/") else BASE / s
            if s.endswith(".json") and cand.exists():
                return cand
        raise SystemExit(f"fetch OK but data file missing: {path}")
    return path


def prep(data_json: Path) -> tuple[str, dict]:
    print(f"[tg_free_digest] prep: {data_json}", file=sys.stderr)
    r = run([PY, str(BASE / "tg_prep.py"), str(data_json)])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or "")
        raise SystemExit(f"tg_prep failed rc={r.returncode}")
    meta = json.loads(data_json.read_text(encoding="utf-8"))
    return r.stdout, meta


def split_prep_by_group(prep_txt: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    cur_key = None
    buf: list[str] = []
    header_re3 = re.compile(r"^##\s+\[([a-z0-9_]+)\]")
    header_re = re.compile(r"^##\s+.*\(`([a-z0-9_]+)`", re.I)
    header_re2 = re.compile(r"^##\s+([a-z0-9_]+)\b", re.I)
    for line in prep_txt.splitlines(True):
        m = header_re3.search(line) or header_re.search(line) or header_re2.search(line)
        if m:
            if cur_key is not None:
                sections[cur_key] = "".join(buf)
            cur_key = m.group(1)
            buf = [line]
        else:
            buf.append(line)
    if cur_key is not None:
        sections[cur_key] = "".join(buf)
    return sections


def free_llm_json(prompt: str, system: str, max_chars: int = 14000) -> dict | None:
    if len(prompt) > max_chars:
        prompt = prompt[: max_chars - 80] + "\n…[truncated]…\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as tf:
        tf.write(prompt)
        user_path = tf.name
    out_path = user_path + ".out.json"
    try:
        cmd = [
            str(FREE_LLM), "-q", "--json",
            "-s", system,
            "-p", '输出 JSON 对象：{"group","title","msg_count","content"}',
            "-f", user_path,
            "-o", out_path,
        ]
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=90)
        if r.returncode != 0:
            sys.stderr.write((r.stderr or r.stdout or "")[-500:] + "\n")
            return None
        return json.loads(Path(out_path).read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"[tg_free_digest] free-llm error: {ex}", file=sys.stderr)
        return None
    finally:
        for p in (user_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def summarize_group(gkey: str, title: str, msg_count: int, section: str, date: str) -> dict:
    if msg_count <= 0 or not section.strip():
        return {"group": gkey, "title": title, "msg_count": msg_count, "content": "无重要内容"}
    if "话题消息" not in section and "### 话题" not in section:
        if not re.search(r"\d{2}:\d{2}\s", section):
            return {"group": gkey, "title": title, "msg_count": msg_count, "content": "无重要内容"}

    prompt = (
        f"群 key={gkey} title={title} msg_count={msg_count} date={date}\n"
        f"prep 行首 HH:MM 属于 {date}；时间 token 必须写成 {{{{{date} HH:MM:SS}}}}，禁止编造其他年份。\n"
        f"根据下面 prep 片段写该群总结。只输出 JSON 对象。\n\n"
        f"===== PREP =====\n{section}\n===== END =====\n"
    )
    doc = free_llm_json(prompt, SYSTEM)
    if not doc or not isinstance(doc, dict):
        return {"group": gkey, "title": title, "msg_count": msg_count, "content": "无重要内容"}
    content = str(doc.get("content") or "").strip() or "无重要内容"
    if re.search(r"别碰|别学|伪造证件|有风险|不推荐|待验证", content) and not re.search(r"^>", content, re.M):
        content = "无重要内容"
    # Fix wrong years in time tokens if model hallucinated
    content = re.sub(
        r"\{\{(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}(?:~\d{2}:\d{2}:\d{2})?)\}\}",
        lambda m: f"{{{{{date} {m.group(2)}}}}}" if m.group(1) != date else m.group(0),
        content,
    )
    return {
        "group": gkey,
        "title": doc.get("title") or title,
        "msg_count": int(doc.get("msg_count") if doc.get("msg_count") is not None else msg_count),
        "content": content,
    }


def short_summary(doc: dict) -> str:
    items = doc.get("items") or []
    with_c = [it for it in items if (it.get("content") or "").strip() not in ("", "无重要内容")]
    lines = [
        f"TG free digest OK  date={doc.get('date')} window={doc.get('window')} partial={doc.get('partial')}",
        f"groups={len(items)} with_content={len(with_c)} total_msgs={sum(int(i.get('msg_count') or 0) for i in items)}",
    ]
    for it in sorted(with_c, key=lambda x: int(x.get("msg_count") or 0), reverse=True)[:8]:
        m = re.search(r"^###\s+(.+)$", it.get("content") or "", re.M)
        topic = (m.group(1) if m else "…")[:48]
        lines.append(f"  - {it.get('title')} ({it.get('msg_count')}): {topic}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", default="last3h")
    ap.add_argument("--date")
    ap.add_argument("--skip-fetch", action="store_true")
    ap.add_argument("--skip-prep", action="store_true")
    ap.add_argument("--push", dest="push", action="store_true", default=False)
    ap.add_argument("--no-push", dest="push", action="store_false")
    ap.add_argument("--out")
    ap.add_argument("--max-groups", type=int, default=0, help="limit groups for debug (0=all)")
    a = ap.parse_args()

    if not FREE_LLM.exists():
        raise SystemExit(f"missing {FREE_LLM}")

    date, label, partial, win_start, win_end, data_path = resolve_window_meta(a.window, a.date)

    if not a.skip_fetch:
        data_path = fetch(a.window, a.date)
    elif not data_path.exists():
        raise SystemExit(f"--skip-fetch but missing {data_path}")

    prep_path = data_path.with_suffix(".txt")
    if a.skip_prep and prep_path.exists():
        prep_txt = prep_path.read_text(encoding="utf-8")
        meta = json.loads(data_path.read_text(encoding="utf-8"))
    else:
        prep_txt, meta = prep(data_path)
        prep_path.write_text(prep_txt, encoding="utf-8")

    w = meta.get("window") or {}
    date = w.get("date") or date
    if "/hourly/" in str(data_path):
        try:
            hh = int(data_path.stem)
            label = f"{hh:02d}-{(hh + 1) if hh < 23 else 24:02d}"
        except ValueError:
            label = w.get("label") or label
    else:
        label = w.get("label") or label
    partial = bool(w.get("partial", partial))
    win_start = w.get("start") or win_start
    win_end = w.get("end") or win_end

    sections = split_prep_by_group(prep_txt)
    if not sections:
        sample = "\n".join(prep_txt.splitlines()[:40])
        print(f"[tg_free_digest] prep header sample (splitter empty):\n{sample[:500]}", file=sys.stderr)

    groups = load_groups()
    msg_by = {g.get("key"): len(g.get("messages") or []) for g in meta.get("groups", [])}

    items = []
    ordered = sorted(groups, key=lambda x: x.get("order") or 999)
    if a.max_groups:
        ordered = ordered[: a.max_groups]
    for i, g in enumerate(ordered, 1):
        k = g["key"]
        sec = sections.get(k, "")
        mc = msg_by.get(k, 0)
        print(f"[tg_free_digest] group {i}/{len(ordered)} {k} msgs={mc} chars={len(sec)}", file=sys.stderr)
        if mc == 0 and not sec.strip():
            items.append({"group": k, "title": g.get("title") or k, "msg_count": 0, "content": "无重要内容"})
            continue
        items.append(summarize_group(k, g.get("title") or k, mc, sec, date))

    doc = {
        "date": date,
        "window": label,
        "partial": partial,
        "win_start": win_start,
        "win_end": win_end,
        "items": items,
    }

    try:
        sys.path.insert(0, str(BASE / "tools"))
        from order import order_doc  # type: ignore
        order_doc(doc)
    except Exception as ex:
        print(f"[tg_free_digest] order_doc skipped: {ex}", file=sys.stderr)

    out_dir = DIGESTS / date
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if "/hourly/" in str(data_path):
        hourly_out = out_dir / "hourly" / f"{data_path.stem}.json"
        window_out = out_dir / f"{label}.json"
        primary = Path(a.out) if a.out else window_out
        for path in {primary.resolve(): primary, hourly_out.resolve(): hourly_out, window_out.resolve(): window_out}.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        push_target = window_out
    else:
        primary = Path(a.out) if a.out else out_dir / f"{label}.json"
        primary.parent.mkdir(parents=True, exist_ok=True)
        primary.write_text(text, encoding="utf-8")
        push_target = primary

    if a.push:
        print(f"[tg_free_digest] push: {push_target}", file=sys.stderr)
        r = run([PY, str(BASE / "tg_digest_push.py"), str(push_target)])
        if r.returncode != 0:
            sys.stderr.write(r.stderr or r.stdout or "")
            print(short_summary(doc))
            print(f"SAVED {push_target} (push FAILED rc={r.returncode})")
            return r.returncode
        print(short_summary(doc))
        print(f"SAVED+PUSHED {push_target}")
        return 0

    print(short_summary(doc))
    print(f"SAVED {push_target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
