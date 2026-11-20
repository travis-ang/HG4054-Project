"""Scrape NBA playoff press-conference transcripts from ASAP Sports.

Two stages:
  python scripts/scrape_asap.py fetch   # download pages into data/raw_html (cached, resumable)
  python scripts/scrape_asap.py parse   # turn cached pages into data/asap_nba_answers.csv

Output: one row per answer turn (a speaker's reply to the preceding question).
"""
import csv
import html
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_html"
OUT = ROOT / "data" / "asap_nba_answers.csv"
BASE = "https://www.asapsports.com/"
YEARS = range(2004, 2027)
DELAY = 1.5  # seconds between requests
UA = "HG4054 student research scraper (NTU Singapore)"

# NBA game press conferences: playoffs, play-in, NBA Cup and regular-season/international
# games. Drops WNBA, All-Star, draft, awards, NCAA. Each event gets a `round` label.
EVENT_RE = re.compile(
    r"^NBA\s+(FINALS|EASTERN|WESTERN|PLAYOFFS|CONFERENCE|PLAY-IN|IN-SEASON TOURNAMENT|SEASON GAME"
    r"|(PARIS|LONDON|MEXICO CITY|BERLIN) GAME)"
    r"|^EMIRATES NBA CUP"
    r"|^(PARIS|MEXICO CITY) GAME:", re.I)

session = requests.Session()
session.headers["User-Agent"] = UA


# ---------------------------------------------------------------- fetching
def fetch(url, name):
    """Return page bytes, using the cache in data/raw_html when present."""
    path = RAW / name
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    for attempt in range(3):
        try:
            time.sleep(DELAY)
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                path.write_bytes(r.content)
                return r.content
            print(f"  HTTP {r.status_code} {url}")
        except requests.RequestException as e:
            print(f"  error {e} {url}")
        time.sleep(5 * (attempt + 1))
    return b""


def links(page, pattern):
    text = page.decode("utf-8", "replace")
    return [(html.unescape(u), html.unescape(t).strip()) for u, t in
            re.findall(r'href="([^"]*' + pattern + r'[^"]*)"[^>]*>([^<]*)', text)]


def stage_fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    seen = set()
    for year in YEARS:
        yp = fetch(f"{BASE}show_year.php?category=11&year={year}", f"year_{year}.html")
        events = [(u, t) for u, t in links(yp, r"show_events\.php") if EVENT_RE.search(t)]
        print(f"{year}: {len(events)} NBA playoff events")
        for eurl, title in events:
            eid = parse_qs(urlparse(eurl).query)["event_id"][0]
            ep = fetch(eurl, f"event_{eid}.html")
            days = {u for u, _ in links(ep, r"show_event\.php\?event_id")}
            for durl in sorted(days):
                q = parse_qs(urlparse(durl).query)
                dname = f"day_{q['event_id'][0]}_{q.get('date', ['x'])[0]}.html"
                dp = fetch(durl, dname)
                for iurl, label in links(dp, r"show_interview\.php\?id="):
                    iid = iurl.split("id=")[-1]
                    if iid in seen:
                        continue
                    seen.add(iid)
                    fetch(f"{BASE}show_interview.php?id={iid}", f"interview_{iid}.html")
            print(f"  {title}: {len(days)} days, {len(seen)} interviews so far")
    print(f"Done. {len(seen)} interviews cached in {RAW}")


# ---------------------------------------------------------------- parsing
MOJI = re.compile(r"[Â-ô][\u0080-ÿŒœŠšŸŽž"
                  r"ƒˆ˜–—‘-„†-•…‰"
                  r"‹›€™]{1,3}")


def fix_text(s):
    """Repair double-encoded UTF-8 (e.g. 'Ã‚Â ' -> ' ') and normalise spaces."""
    for _ in range(3):
        def repl(m):
            try:
                return m.group(0).encode("cp1252").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                return m.group(0)
        new = MOJI.sub(repl, s)
        if new == s:
            break
        s = new
    s = s.replace("Â", "")  # stray Â left from nbsp mangling
    s = re.sub(r"[   ]", " ", s)
    s = s.replace("‑", "-")
    s = re.sub(r"[\u0080-\u009f]", " ", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def strip_tags(s):
    return fix_text(html.unescape(re.sub(r"<[^>]+>", "", s)))


SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z0-9 .,'’\-]{1,40}?)\s*:\s*(.*)$")
# a word in a speaker label is all caps, or a capitalised prefix + caps: McCOLLUM, LeBRON, DeROZAN
LABEL_WORD = re.compile(r"^(?:[A-Z0-9.,'’\-]+|[A-Z][a-z]{1,2}[A-Z][A-Z.'’\-]*)$")


def is_speaker_label(label):
    words = label.split()
    return (bool(words) and not label.strip(" .").isdigit()
            and any(c.isupper() for c in label)
            and all(LABEL_WORD.match(w) for w in words))
Q_RE = re.compile(r"^Q\s*[.:]\s*(.*)$")

ROUND_PATTERNS = [
    (r"PLAY-IN", "play_in"),
    (r"IN-SEASON TOURNAMENT|NBA CUP", "nba_cup"),
    (r"PARIS|LONDON|MEXICO CITY|BERLIN|SEASON GAME", "regular_season_special"),
    (r"CONFERENCE FINALS", "conference_finals"),
    (r"SEMIFINAL|ROUND TWO|SECOND ROUND", "conference_semifinals"),
    (r"FIRST ROUND|ROUND ONE", "first_round"),
    (r"^NBA FINALS", "finals"),
]


def round_of(title):
    t = title.upper()
    for pat, name in ROUND_PATTERNS:
        if re.search(pat, t):
            return name
    return "other"


END_MARKERS = ["FastScripts Transcript by ASAP Sports", "FastScripts by ASAP Sports",
               "End of FastScripts",
               "About ASAP Sports", "FastScripts Archive"]


def session_of(game_info):
    g = game_info.lower()
    if "postgame" in g or "post-game" in g or "post game" in g:
        return "postgame"
    if "pregame" in g or "pre-game" in g or "shootaround" in g:
        return "pregame"
    if "practice" in g or "media day" in g or "off day" in g:
        return "practice"
    if re.search(r"game\s+(one|two|three|four|five|six|seven|\d)", g):
        return "postgame_probable"  # older pages only say e.g. "Game Six"
    return "unknown"


def parse_interview(iid, raw):
    page = raw.decode("utf-8", "replace")
    start = page.find("<h1>")
    if start < 0:
        return []
    # transcripts end with one of these markers depending on the era of the page
    ends = [page.find(m, start) for m in END_MARKERS]
    ends = [e for e in ends if e > 0]
    block = page[start:min(ends) if ends else len(page)]

    event = strip_tags((re.search(r"<h1>(.*?)</h1>", block, re.S) or [None, ""])[1])
    date = strip_tags((re.search(r"<h2>(.*?)</h2>", block, re.S) or [None, ""])[1])
    h3s = re.findall(r"<h3>(.*?)</h3>", block, re.S)
    listed = [strip_tags(h) for h in h3s if "show_player" in h]
    other_h3 = [strip_tags(h) for h in h3s if "show_player" not in h]
    italics = [strip_tags(i) for i in re.findall(r"<i>(.*?)</i>", block, re.S)]
    team = other_h3[0] if other_h3 else ""
    game_info = " | ".join([x for x in other_h3[1:] + italics if x])

    # body: everything after the last header tag
    last_hdr = max(block.rfind("</h3>"), block.rfind("</h2>"), block.rfind("</i>"))
    body = block[last_hdr:]
    body = re.sub(r"(?i)<br\s*/?>|</p>|<p[^>]*>", "\n", body)
    lines = [strip_tags(l) for l in body.split("\n")]
    lines = [l for l in lines if l]

    preamble, turns = [], []
    question, cur = "", None  # cur = [speaker, question, text]
    for line in lines:
        mq = Q_RE.match(line)
        ms = SPEAKER_RE.match(line)
        if mq:
            if cur:
                turns.append(cur)
                cur = None
            question = mq.group(1)
        elif ms and is_speaker_label(ms.group(1)):
            if cur:
                turns.append(cur)
            cur = [ms.group(1).strip(" .").upper(), question, ms.group(2)]
        elif cur:
            cur[2] += " " + line            # continuation of an answer
        elif question:
            question += " " + line          # question running over several lines
        else:
            preamble.append(line)           # score line etc. before first Q
    if cur:
        turns.append(cur)

    y = re.search(r"(\d{4})", date)
    rows = []
    for k, (spk, q, a) in enumerate(turns):
        rows.append({
            "interview_id": iid,
            "turn": k,
            "year": y.group(1) if y else "",
            "date": date,
            "event": event,
            "round": round_of(event),
            "game_info": game_info,
            "session": session_of(game_info),
            "score_line": " | ".join(preamble[:3]),
            "listed_speakers": "; ".join(listed),
            "listed_team": team,
            "speaker": spk,
            "is_coach_label": int(spk.upper().startswith("COACH")),
            "question": q.strip(),
            "answer": a.strip(),
            "n_words": len(a.split()),
            "url": f"{BASE}show_interview.php?id={iid}",
        })
    return rows


def stage_parse():
    files = sorted(RAW.glob("interview_*.html"), key=lambda p: int(p.stem.split("_")[1]))
    fields = ["interview_id", "turn", "year", "date", "event", "round", "game_info",
              "session", "score_line", "listed_speakers", "listed_team", "speaker",
              "is_coach_label", "question", "answer", "n_words", "url"]
    n_rows = n_empty = 0
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for p in files:
            rows = parse_interview(p.stem.split("_")[1], p.read_bytes())
            if not rows:
                n_empty += 1
            for r in rows:
                w.writerow(r)
            n_rows += len(rows)
    print(f"{len(files)} interviews -> {n_rows} answer rows ({n_empty} with no turns) -> {OUT}")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else ""
    if stage == "fetch":
        stage_fetch()
    elif stage == "parse":
        stage_parse()
    else:
        print(__doc__)
