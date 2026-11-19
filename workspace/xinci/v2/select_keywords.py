import re

try:
    from v2.extract_video import GENERIC_VIDEO_SEEDS, is_generic_video_phrase
except ImportError:  # pragma: no cover
    GENERIC_VIDEO_SEEDS = frozenset({
        "capcut ai template",
        "ai photo to video",
        "capcut ai lab",
        "ai video trend",
    })

    def is_generic_video_phrase(phrase: str) -> bool:
        return (phrase or "").strip().lower() in GENERIC_VIDEO_SEEDS

DERIVED_SUF = re.compile(r"^(?P<base>.+?)\s+(unblocked|online|play|alternative|ai)$", re.I)

EVERGREEN_GAMES = {
    "counter-strike 2",
    "cs2",
    "dota 2",
    "escape from tarkov",
    "apex legends",
    "pubg",
    "pubg battlegrounds",
    "warframe",
    "grand theft auto v",
    "gta v",
    "euro truck simulator 2",
    "final fantasy xiv",
    "final fantasy xiv online",
    "steam deck",
    "steam frame",
    "steam controller",
    "adopt me",
    "adopt me!",
    "99 nights in the forest",
    "anime adventures",
    "disney dreamlight valley",
    "disney dreamlight valley the keepsake sea",
    "call of duty",
    "marvel rivals",
    "mahjong soul",
    "football manager",
    "wuthering waves",
    "limbus company",
}


def _normalize_game_name(name: str) -> str:
    low = (name or "").lower()
    cleaned = re.sub(r"[^\w\s]", " ", low)
    return re.sub(r"\s+", " ", cleaned).strip()


def primary_source(src: str) -> str:
    return (src or "").split("/")[0].strip()


def _qualified(e) -> bool:
    phrase = (e.get("phrase") or "").strip()
    evidence = e.get("evidence")
    names = e.get("names")
    return bool(phrase and (evidence or names))


def filter_derived(entries: list[dict]) -> list[dict]:
    phrases = {(e.get("phrase") or "").strip() for e in entries if e.get("phrase")}
    lower = {p.lower() for p in phrases}
    result = []
    for e in entries:
        p = (e.get("phrase") or "").strip()
        if not p:
            continue
        m = DERIVED_SUF.match(p)
        if m:
            base = m.group("base").strip()
            if base.lower() in lower:
                continue
        result.append(e)
    return result


def _is_evergreen_game(phrase: str) -> bool:
    norm = _normalize_game_name(phrase)
    if not norm:
        return False
    evergreen_norm = {_normalize_game_name(x) for x in EVERGREEN_GAMES}
    if norm in evergreen_norm:
        return True
    # prefix match only for stems that are clearly the same franchise head
    for ev in ("call of duty", "football manager", "ea sports fc", "euro truck simulator"):
        evn = _normalize_game_name(ev)
        if norm == evn or norm.startswith(evn + " "):
            return True
    return False


def _is_seed_or_anchor(e: dict) -> bool:
    if e.get("role") == "anchor" or e.get("from") == "seed":
        return True
    return is_generic_video_phrase(e.get("phrase") or "")


def _bucket(e: dict) -> str:
    src = primary_source(e.get("source") or "")
    track = str(e.get("track") or "").lower()
    if src.startswith("书签X") or src.startswith("书签x"):
        return "x"
    if src == "热梗轨" or track in {"video", "热梗", "meme"} or "热梗" in src:
        return "video"
    if src == "游戏轨" or track in {"game", "游戏"} or "游戏" in src:
        return "game"
    if src == "AI工具轨" or "ai工具" in src.lower() or track in {"ai", "ai_tools"}:
        return "ai"
    if src == "新闻轨" or track in {"news", "新闻"}:
        return "news"
    if src == "Higgsfield" or "higgsfield" in src.lower():
        return "higgsfield"
    # test fixtures use english source prefixes
    if src.lower().startswith("video"):
        return "video"
    if src.lower().startswith("game") or src.lower().startswith("steam"):
        return "game"
    return "other"


def _is_headlineish(e: dict) -> bool:
    phrase = (e.get("phrase") or "").strip()
    src = primary_source(e.get("source") or "")
    if src != "新闻轨" and "news" not in src.lower():
        return False
    low = phrase.lower()
    if low.startswith("the ") and len(phrase.split()) >= 3:
        return True
    if low.startswith("quoting ") or "fundraiser" in low:
        return True
    if len(phrase.split()) >= 5:
        return True
    return False


def _prefer_event(e: dict) -> int:

    blob = f"{e.get('evidence') or ''} {e.get('source') or ''}".lower()
    score = 0
    for kw in ("up-and-coming", "新热", "is_new", "new_on_chart", "reheating", "首发", "launch"):
        if kw in blob:
            score += 1
    return score


def select_board_keywords(entries, cap=40, game_reserve=10, video_reserve=10, x_max=5) -> list[dict]:
    filtered = filter_derived([e for e in (entries or []) if isinstance(e, dict)])
    seen = set()
    deduped = []
    for e in filtered:
        p = (e.get("phrase") or "").strip()
        if not p:
            continue
        key = p.lower()
        if key in seen:
            continue
        if not _qualified(e) or _is_seed_or_anchor(e):
            continue
        seen.add(key)
        deduped.append(e)

    buckets = {"x": [], "video": [], "game": [], "ai": [], "news": [], "higgsfield": [], "other": []}
    for e in deduped:
        buckets[_bucket(e)].append(e)

    def x_sort_key(e):
        ev = str(e.get("evidence") or "").lower()
        official = 0 if any(k in ev for k in ("official", "launch", "首发", "官方")) else 1
        return (official, 0)

    x_entries = sorted(buckets["x"], key=x_sort_key)
    selected_x = x_entries[:x_max]

    game_ok = []
    for e in buckets["game"]:
        if _is_evergreen_game(e.get("phrase") or ""):
            continue
        game_ok.append(e)
    game_ok.sort(key=_prefer_event, reverse=True)
    selected_games = game_ok[:game_reserve]

    selected_video = buckets["video"][:video_reserve]

    chosen = []
    seen_p = set()

    def add(items):
        for e in items:
            p = (e.get("phrase") or "").strip().lower()
            if not p or p in seen_p:
                continue
            if len(chosen) >= cap:
                return
            seen_p.add(p)
            chosen.append(e)

    add(selected_x)
    add(selected_video)
    add(selected_games)

    # Remaining slots: other tracks with evidence only. Do not exceed game/video/x reserves.
    leftovers = []
    for key in ("ai", "news", "higgsfield", "other"):
        leftovers.extend(buckets[key])

    qualified_left = []
    for e in leftovers:
        p = (e.get("phrase") or "").strip()
        if not p or p.lower() in seen_p:
            continue
        if _is_evergreen_game(p) or _is_seed_or_anchor(e) or _is_headlineish(e):
            continue
        if not _qualified(e):
            continue
        qualified_left.append(e)
    add(qualified_left)
    return chosen


if __name__ == "__main__":
    entries = []
    for i in range(4):
        entries.append({"phrase": f"video play {i}", "source": "热梗轨", "evidence": "yes", "track": "video"})
    for g in ["Counter-Strike 2", "Dota 2", "AION 2", "Hades II", "Roblox Upstart"] + [f"Evergreen Game {i}" for i in range(25)]:
        ev = "Up-and-Coming" if g in {"AION 2", "Hades II", "Roblox Upstart"} else "chart listing"
        entries.append({"phrase": g, "source": "游戏轨", "evidence": ev, "track": "game"})
    for a in ["Foo ai", "Foo", "Genie 4 ai", "Genie 4", "CapCut AI template"] + [f"AI Tool {i}" for i in range(25)]:
        entries.append({"phrase": a, "source": "AI工具轨", "evidence": "tech", "track": "ai"})
    res = select_board_keywords(entries)
    phrases = [e["phrase"].lower() for e in res]
    assert sum(1 for e in res if primary_source(e.get("source")) == "热梗轨") == 4
    assert "counter-strike 2" not in phrases and "dota 2" not in phrases
    assert "foo ai" not in phrases and "capcut ai template" not in phrases
    assert len([e for e in res if primary_source(e.get("source")) == "游戏轨"]) <= 10
    assert len(res) <= 40
    res2 = select_board_keywords([
        {"phrase": "New Game A", "source": "游戏轨", "evidence": "Up-and-Coming"},
        {"phrase": "New Game B", "source": "游戏轨", "evidence": "Up-and-Coming"},
        {"phrase": "AI Tool X", "source": "AI工具轨", "evidence": "release"},
        {"phrase": "AI Tool Y", "source": "AI工具轨", "evidence": "release"},
    ])
    assert len(res2) == 4, len(res2)
    res3 = select_board_keywords([
        {"phrase": "CapCut AI template", "source": "热梗轨", "evidence": "seed", "from": "seed"},
        {"phrase": "AI photo to video", "source": "热梗轨", "evidence": "seed"},
    ])
    assert res3 == []
    print("Self-check passed successfully.")
