import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
d = json.loads(p.read_text(encoding="utf-8"))
import re
pat = re.compile(chr(123)+chr(123)+r"[^{}"+chr(10)+"]{4,40}"+chr(125)+chr(125))
for it in d.get("items", []):
    c = it.get("content") or ""
    it["content"] = pat.sub("", c)
    # also collapse leftover double spaces around middot? leave as-is
p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + chr(10), encoding="utf-8")
print("stripped", p)
