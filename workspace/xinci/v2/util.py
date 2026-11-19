from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os
import unicodedata
import re

HERE = Path(__file__).resolve().parents[1]
BJ = timezone(timedelta(hours=8))

def now_bj() -> datetime:
    return datetime.now(BJ)

def bj_stamp(dt=None) -> str:
    if dt is None:
        dt = now_bj()
    return dt.astimezone(BJ).strftime("%Y-%m-%d %H:%M")

def today_bj() -> str:
    return now_bj().strftime("%Y-%m-%d")

def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = p.with_suffix(p.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1
)
    tmp_path.replace(p)

def norm(s) -> str:
    if not isinstance(s, str):
        s = str(s)
    s = unicodedata.normalize("NFKC", s)
    # Remove bracketed content and brackets: strip （(【[ ... ]】)）
    # We can iteratively or pattern-wise remove characters matching brackets and their contents or just strip specific chars.
    # The prompt says: strip （(【[ ... ]】)）, NFKC, lower, remove non-alnum
    # Usually merge_board removes specific enclosing marks or normalizes them. Let's strip brackets/parentheses and their contents or just remove those characters.
    # Looking at "strip （(【[ ... ]】)）", it usually means remove these specific punctuation marks or contents inside.
    # Let's remove characters: （, ), (, ）, 【, 】, [, ], and normalize whitespace.
    # Actually, removing non-alnum at the end handles most punctuation, but let's explicitly remove bracket chars or contents if needed.
    # Let's replace brackets and contents, or just remove the bracket characters. "strip" might mean remove the characters or content. 
    # Let's remove characters matching full-width/half-width brackets and parentheses, then lower, then non-alnum.
    # Wait, "strip （(【[ ... ]】)）" often means regex sub or translation table. Let's do a translate for brackets or regex.
    # Let's remove characters: ( ) （ ） 【 】 [ ]
    trans = str.maketrans("", "", "()（）【】[]")
    s = s.translate(trans)
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum())
    return s

def load_dotenv(path=None):
    if path is None:
        path = HERE / ".env"
    p = Path(path)
    loaded_keys = []
    if not p.exists():
        return loaded_keys
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    # Remove surrounding quotes if any
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = val
                    loaded_keys.append(key)
    except Exception:
        pass
    return loaded_keys


def data_root() -> Path:
    env = os.environ.get("XINCI_HOME")
    if env:
        return Path(env)
    return HERE


def xinci_home() -> Path:
    return data_root()
