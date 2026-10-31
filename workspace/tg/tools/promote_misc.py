#!/usr/bin/env python3
"""Normalize misc buckets for TG digests (aligned 架构总工 + Grok总管 2026-10-31).

Rules:
1. At most one `### 零星消息` per group per hour section (kept last).
2. Contextual short replies (追问/补充/找到原因) merge into the neighboring topic.
3. Do NOT invent named topics for 1–2 chitchat lines; leftovers go into 零星消息.
4. `### 无实质主题` is an alias of 零星消息 (collapsed into 零星消息).
5. Schema unchanged: ### topics + ### 零星消息 + > speech {{time}}.

Usage:
  promote_content(md) -> md
  promote_doc(doc) mutates items[].content
  CLI: python3 tools/promote_misc.py FILE.json [...]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOPIC_HEAD = re.compile(
    r"^###\s+(.*?)\s*(?:[（(]\s*(\d+)\s*条\s*/\s*(\d+)\s*人\s*[)）])?\s*$"
)
SPEECH = re.compile(r"^>\s*([^：:\n]{1,40}?)\s*[：:]\s*(.*)$")
HOUR = re.compile(r"^\*\*\d{1,2}:\d{2}\s*[–-]\s*\d{1,2}:\d{2}\*\*$")
SEC = re.compile(r"^#{1,2}\s+")
VH = re.compile(r"^#{1,4}\s+.*网上核验")
CHIP = re.compile(r"^~\s*涉及商家")
ACTIVE = re.compile(r"^~\s*话题活跃成员")
SUMMARY = re.compile(r"^~\s*摘要[：:]")
MISC_TITLES = {"零星消息", "无实质主题", "其他", "闲聊"}

BRAND_RE = re.compile(
    r"(?i)\b("
    r"maxx|m1|giffgaff|tello|cmhk|csl|smartone|vodafone|lebara|voxi|lyca|t-?mobile|att|verizon|"
    r"wise|monzo|starling|revolut|n26|zopa|zilch|cashi|chase|citi|amex|capital\s*one|\bc1\b|"
    r"za\s*bank|众安|汇丰|hsbc|ibkr|盈透|嘉信|schwab|星展|dbs|airstar|天星|"
    r"binance|币安|okx|bybit|bitget|gate|mexc|kraken|dtcpay|dtc|wirex|bridge|花生|"
    r"paypal|paysend|plum|sendwave|trezor|"
    r"vps|家宽|搬瓦工|vultr|hetzner|racknerd|甲骨文|oracle|zorocloud|索隆|干杯云|dig\b|"
    r"substore|sub-store|3x-?ui|loon|surge|clash|shadowrocket|egern|"
    r"claude|chatgpt|codex|esim|itin|ssn|nubank|紫卡|红包卡"
    r")\b|"
    r"(众安|花生|万里汇|工银|汇立|紫卡|红包卡|家宽|搬瓦工|索隆|干杯云|盈透|嘉信|天星|数码通)"
)

CONT_RE = re.compile(r"找到原因|关了|搞定了|好了|原来是|解决了|改回到|那我|修好|关掉|继续|刚才|上面|同上")


def _speakers_and_text(lines: list[str]) -> tuple[set[str], str, list[str]]:
    speakers, texts, speeches = set(), [], []
    for ln in lines:
        m = SPEECH.match(ln.strip())
        if not m:
            continue
        speakers.add(m.group(1).strip())
        body = re.sub(r"\s*\{\{[^}]+\}\}\s*$", "", m.group(2).strip()).strip()
        texts.append(body)
        speeches.append(ln)
    return speakers, " ".join(texts), speeches


def _count_nm(speeches: list[str]) -> tuple[int, int]:
    speakers = set()
    n = 0
    for ln in speeches:
        m = SPEECH.match(ln.strip())
        if not m:
            continue
        n += 1 + ln.count(" · ")
        speakers.add(m.group(1).strip())
    return max(n, len(speeches)), max(len(speakers), 1 if speeches else 0)


def _brand_hits(text: str) -> list[str]:
    hits, seen = [], set()
    for m in BRAND_RE.finditer(text):
        key = m.group(0).lower()
        if key in seen:
            continue
        seen.add(key)
        hits.append(m.group(0))
    return hits


def _title_base(heading: str) -> str:
    m = TOPIC_HEAD.match(heading.strip())
    title = (m.group(1) if m else heading.replace("###", "").strip()).strip()
    return re.sub(r"\s*[（(]\s*\d+\s*条.*$", "", title).strip()


def _is_misc_title(heading: str) -> bool:
    base = _title_base(heading)
    return base in MISC_TITLES or base.startswith("零星")


def _should_merge_into_prev(prev: dict | None, body_lines: list[str]) -> bool:
    if not prev or _is_misc_title(prev.get("heading") or ""):
        return False
    speakers, joined, speeches = _speakers_and_text(body_lines)
    if not speeches:
        return False
    prev_speakers, prev_text, _ = _speakers_and_text(prev["lines"])
    share_speaker = bool(speakers & prev_speakers)
    cont = bool(CONT_RE.search(joined))
    share_brand = bool(set(x.lower() for x in _brand_hits(joined)) & set(x.lower() for x in _brand_hits(prev_text + " " + (prev.get("heading") or ""))))
    # Contextual follow-up: same speaker continuing, or same brand + same speaker thread
    return (share_speaker and cont) or (share_speaker and share_brand)


def _refresh_topic_heading(block: dict) -> None:
    if _is_misc_title(block["heading"]):
        block["heading"] = "### 零星消息"
        return
    base = _title_base(block["heading"])
    speeches = [ln for ln in block["lines"] if SPEECH.match(ln.strip())]
    n, m = _count_nm(speeches)
    if n:
        block["heading"] = f"### {base} ({n} 条 / {m} 人)"


def promote_content(content: str) -> str:
    if not content or content.strip() in ("无重要内容", "无实质内容"):
        return content
    lines = content.split("\n")
    blocks: list[dict] = []
    buf_kind = "pre"
    buf_head = ""
    buf_lines: list[str] = []

    def flush():
        nonlocal buf_kind, buf_head, buf_lines
        if buf_kind == "pre":
            if buf_lines:
                blocks.append({"kind": "pre", "heading": "", "lines": buf_lines[:]})
        elif buf_kind == "topic":
            blocks.append({"kind": "topic", "heading": buf_head, "lines": buf_lines[:]})
        elif buf_kind == "verify":
            if buf_lines:
                blocks.append({"kind": "verify", "heading": "", "lines": buf_lines[:]})
        buf_lines = []

    def is_verify_start(s: str) -> bool:
        s = s.strip()
        return bool(VH.match(s) or (s.startswith("---") and "核验" in s))

    i = 0
    while i < len(lines):
        ln = lines[i]
        if is_verify_start(ln):
            flush()
            buf_kind = "verify"
            buf_lines = [ln]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if HOUR.match(nxt.strip()) or TOPIC_HEAD.match(nxt.strip()) or (
                    SEC.match(nxt.strip()) and not TOPIC_HEAD.match(nxt.strip()) and not VH.match(nxt.strip())
                ):
                    break
                buf_lines.append(nxt)
                i += 1
            flush()
            buf_kind = "pre"
            continue
        if HOUR.match(ln.strip()) or (SEC.match(ln.strip()) and not TOPIC_HEAD.match(ln.strip())):
            flush()
            blocks.append({"kind": "pre", "heading": "", "lines": [ln]})
            buf_kind = "pre"
            buf_lines = []
            i += 1
            continue
        hm = TOPIC_HEAD.match(ln.strip())
        if hm:
            flush()
            buf_kind = "topic"
            buf_head = ln.strip()
            buf_lines = []
            i += 1
            continue
        buf_lines.append(ln)
        i += 1
    flush()

    # Pass 1: merge contextual misc into previous concrete topic; else keep as misc
    rebuilt: list[dict] = []
    for b in blocks:
        if b["kind"] != "topic":
            rebuilt.append(b)
            continue
        if not _is_misc_title(b["heading"]):
            rebuilt.append({"kind": "topic", "heading": b["heading"], "lines": b["lines"][:]})
            continue
        prev = next((x for x in reversed(rebuilt) if x["kind"] == "topic"), None)
        meta = [ln for ln in b["lines"] if not SPEECH.match(ln.strip()) and ln.strip() and not SUMMARY.match(ln.strip())]
        keep_misc: list[str] = []
        for ln in b["lines"]:
            if not SPEECH.match(ln.strip()):
                continue
            if _should_merge_into_prev(prev, [ln]):
                prev["lines"].append(ln)
                _refresh_topic_heading(prev)
            else:
                keep_misc.append(ln)
        if keep_misc or meta:
            # Leftover misc → standard 零星消息 bucket (do not invent topic names)
            rebuilt.append({"kind": "topic", "heading": "### 零星消息", "lines": keep_misc + [ln for ln in meta if not CHIP.match(ln.strip())]})

    # Pass 2: within each hour segment (or whole doc), collapse multiple 零星/无实质 into one at end of segment
    final: list[dict] = []
    seg_topics: list[dict] = []
    seg_misc_lines: list[str] = []

    def flush_seg():
        nonlocal seg_topics, seg_misc_lines
        final.extend(seg_topics)
        if seg_misc_lines:
            # dedupe identical speech lines while preserving order
            seen, speeches, meta = set(), [], []
            for ln in seg_misc_lines:
                if SPEECH.match(ln.strip()):
                    key = ln.strip()
                    if key in seen:
                        continue
                    seen.add(key)
                    speeches.append(ln)
                elif ln.strip() and not SUMMARY.match(ln.strip()):
                    meta.append(ln)
            if speeches or meta:
                final.append({"kind": "topic", "heading": "### 零星消息", "lines": speeches + meta})
        seg_topics, seg_misc_lines = [], []

    for b in rebuilt:
        if b["kind"] == "pre" and b["lines"] and HOUR.match(b["lines"][0].strip()):
            flush_seg()
            final.append(b)
            continue
        if b["kind"] != "topic":
            # verify / other pre: flush misc before verify so 零星 stays before 核验
            if b["kind"] == "verify":
                if seg_misc_lines:
                    seen, speeches, meta = set(), [], []
                    for ln in seg_misc_lines:
                        if SPEECH.match(ln.strip()):
                            key = ln.strip()
                            if key in seen:
                                continue
                            seen.add(key)
                            speeches.append(ln)
                        elif ln.strip() and not SUMMARY.match(ln.strip()):
                            meta.append(ln)
                    if speeches or meta:
                        final.extend(seg_topics)
                        final.append({"kind": "topic", "heading": "### 零星消息", "lines": speeches + meta})
                        seg_topics, seg_misc_lines = [], []
                    else:
                        final.extend(seg_topics)
                        seg_topics = []
                else:
                    final.extend(seg_topics)
                    seg_topics = []
            final.append(b)
            continue
        if _is_misc_title(b["heading"]):
            seg_misc_lines.extend(b["lines"])
        else:
            _refresh_topic_heading(b)
            seg_topics.append(b)
    flush_seg()

    out: list[str] = []
    for b in final:
        if b["kind"] == "topic":
            out.append(b["heading"])
            out.extend(b["lines"])
        else:
            out.extend(b["lines"])

    text_out = "\n".join(out)
    text_out = re.sub(r"\n{3,}", "\n\n", text_out).strip()
    if content.endswith("\n"):
        text_out += "\n"
    return text_out


def promote_doc(doc: dict) -> dict:
    for it in doc.get("items") or []:
        c = it.get("content")
        if isinstance(c, str) and c.strip() and c.strip() != "无重要内容":
            it["content"] = promote_content(c)
    return doc


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: promote_misc.py FILE.json [...]", file=sys.stderr)
        return 2
    for path in argv[1:]:
        p = Path(path)
        doc = json.loads(p.read_text(encoding="utf-8"))
        before = json.dumps(doc, ensure_ascii=False)
        promote_doc(doc)
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from order import order_doc  # type: ignore
            order_doc(doc)
        except Exception as ex:
            print(f"[promote_misc] order_doc skipped: {ex}", file=sys.stderr)
        after = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        if after != before:
            p.write_text(after, encoding="utf-8")
            print(f"updated {p}")
        else:
            print(f"unchanged {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
