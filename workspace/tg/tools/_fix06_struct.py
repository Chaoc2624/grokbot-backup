import json, re
from pathlib import Path
print("loadok")
SPEECH = re.compile(r"^>\s*([^：:\n]+)[：:](.*)$")
MID = re.compile(r"\s*\{\{([^{}\n]{4,40})\}\}")
JOIN = re.compile(r" · ([^·：:\n]{1,40})[：:]")

def fix(content):
    if not content or content.strip() == "无重要内容":
        return content
    out = []
    for line in content.split("\n"):
        m = SPEECH.match(line)
        if not m:
            if line.startswith(">") and "：" not in line and ":" in line:
                line = line.replace(":", "：", 1)
                m = SPEECH.match(line)
            if not m:
                out.append(line)
                continue
        sp, body = m.group(1), m.group(2)
        body2 = MID.sub("", body)
        parts = []
        cur = sp
        buf = []
        i = 0
        while True:
            mm = JOIN.search(body2, i)
            if not mm:
                buf.append(body2[i:])
                break
            buf.append(body2[i:mm.start()])
            t = "".join(buf).strip(" ·")
            if t:
                parts.append((cur, t))
            cur = mm.group(1).strip()
            buf = []
            i = mm.end()
        t = "".join(buf).strip(" ·")
        if t:
            parts.append((cur, t))
        if not parts:
            out.append("> %s：%s" % (sp, MID.sub("", body).rstrip()))
            continue
        for a, b in parts:
            out.append("> %s：%s" % (a, b))
    lines = [ln for ln in out if not ln.startswith("> XboxUI")]
    return MID.sub("", "\n".join(lines))

def main():
    paths = [
        Path("digests/2026-10-30/hourly/06.json"),
        Path("digests/2026-10-30/06-07.json"),
    ]
    for p in paths:
        if not p.exists():
            print("skip missing", p)
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        nfix = 0
        for it in d.get("items", []):
            c = it.get("content") or ""
            nc = fix(c)
            if nc != c:
                it["content"] = nc
                nfix += 1
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("wrote", p, "items_fixed", nfix)

if __name__ == "__main__":
    main()
