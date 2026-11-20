"""Fetch All-Star selections and NBA head coaches from Wikipedia (MediaWiki API).

python scripts/fetch_labels.py

Writes:
  data/allstars.csv   player, season          one row per All-Star selection (incl. selected-but-injured)
  data/allnba.csv     player, season          one row per All-NBA (1st/2nd/3rd team) selection
  data/coaches.csv    coach, team, first_season, last_season
Season = the year the season ends (2024 = 2023-24 season, All-Star Game Feb 2024, Finals June 2024).
Raw API responses are cached in data/raw_wiki/.
"""
import csv
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_wiki"
UA = "HG4054StudentProject/1.0 (NTU course project)"
API = "https://en.wikipedia.org/w/api.php?action=parse&prop=wikitext&format=json&formatversion=2&redirects=1&page="
CURRENT_SEASON = 2026

TEAMS = ["Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls",
         "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons",
         "Golden State Warriors", "Houston Rockets", "Indiana Pacers", "Los Angeles Clippers",
         "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat", "Milwaukee Bucks",
         "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks", "Oklahoma City Thunder",
         "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
         "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards"]


def wikitext(title):
    path = RAW / (re.sub(r"\W+", "_", title) + ".json")
    if path.exists() and not path.read_text(encoding="utf-8").startswith("{"):
        path.unlink()  # cached rate-limit/error page
    for attempt in range(4):
        if path.exists():
            break
        time.sleep(5 * (attempt + 1))  # Wikimedia asks for slow, serial requests
        subprocess.run(["curl", "-s", "-A", UA, "-o", str(path), API + quote(title.replace(" ", "_"))],
                       check=True, timeout=60)
        if not path.read_text(encoding="utf-8").startswith("{"):
            path.unlink()
    if not path.exists():
        print(f"  failed: {title}")
        return ""
    j = json.loads(path.read_text(encoding="utf-8"))
    if "error" in j:
        print(f"  missing page: {title}")
        return ""
    return j["parse"]["wikitext"]


def first_name(row):
    m = re.search(r"\{\{sortname\|([^|}]+)\|([^|}]+)", row)
    if m:
        return f"{m.group(1).strip()} {m.group(2).strip()}"
    for target, label in re.findall(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", row):
        if re.match(r"(File|Image|\d{4})", target) or "season" in target.lower() or "NBA" in target:
            continue
        return (label or target).strip()
    return None


# ------------------------------------------------------------------ All-Stars
def parse_years(cell):
    """'[[2005 NBA All-Star Game|2005]]–[[2026 ...|2026]], [[2028 ...|2028]]' -> [2005..2026, 2028]"""
    cell = re.sub(r"\[\[[^\]|]*\|(\d{4})\]\]", r"\1", cell)
    cell = re.sub(r"\[\[(\d{4})[^\]]*\]\]", r"\1", cell)
    cell = re.sub(r"<ref.*?(</ref>|/>)|\{\{.*?\}\}", "", cell)
    years = set()
    for a, b in re.findall(r"(\d{4})\s*(?:[–-]\s*(\d{4}))?", cell):
        a = int(a)
        years.update(range(a, int(b) + 1) if b else [a])
    return sorted(years)


def allstars():
    w = wikitext("List of NBA All-Stars")
    rows = []
    for row in w.split("\n|-"):
        row = row.split("\n|}")[0]                                # stop at the end of the table (notes follow)
        row = re.sub(r"<ref.*?(</ref>|/>)", "", row, flags=re.S)   # citations are not players
        if "All-Star Game" not in row:
            continue
        name = first_name(row)
        cells = re.split(r"\|\||\n\|", row)
        sel = next((c for c in cells if "All-Star Game" in c), "")
        if name:
            for y in parse_years(sel):
                if 1951 <= y <= CURRENT_SEASON:   # drops citation years parsed by mistake
                    rows.append((name, y))
    return rows


# ------------------------------------------------------------------ All-NBA
def allnba():
    """Each season block starts with {{nbay|YYYY}} (season start year); players follow a flag icon."""
    w = wikitext("All-NBA Team")
    rows, season = [], None
    pat = re.compile(r"\{\{nbay\|(\d{4})[^}]*\}\}|\{\{flagicon\|[^}]*\}\}\s*(?:''')?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    for m in pat.finditer(w):
        if m.group(1):
            season = int(m.group(1)) + 1
        elif season:
            rows.append(((m.group(3) or m.group(2)).strip(), season))
    return rows


# ------------------------------------------------------------------ coaches
def coach_span(row):
    row = re.sub(r"<ref.*?(</ref>|/>)", "", row, flags=re.S)
    starts = [int(y) + 1 for y in re.findall(r"\{\{nba[a-z]*\|(\d{4})", row)]    # {{nbats|2013..}}/{{nbay|2004..}}: season start -> end year
    if not starts:  # fall back to plain season text such as [[2013–14 ... season|2013–14]]
        starts = [int(a) + 1 for a, _ in re.findall(r"(\d{4})[–-](\d{2,4})", row)]
    if not starts:
        return None
    last = CURRENT_SEASON if "present" in row.lower() else max(starts)
    return min(starts), last


def coaches():
    rows = []
    for team in TEAMS:
        w = wikitext(f"List of {team} head coaches")
        tables = "\n".join(re.findall(r"\{\|.*?\n\|\}", w, flags=re.S))  # table rows only, not prose
        n = 0
        for row in tables.split("\n|-"):
            if "sortname" not in row and "[[" not in row:
                continue
            name, span = first_name(row), coach_span(row)
            if name and span and span[1] >= 2003:
                rows.append((name, team, span[0], span[1]))
                n += 1
        print(f"  {team}: {n} coaches since 2003")
    return rows


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    a = allstars()
    with open(ROOT / "data" / "allstars.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["player", "season"])
        w.writerows(sorted(set(a)))
    print(f"All-Star selections: {len(set(a))} ({len({n for n, _ in a})} players)")
    n = allnba()
    with open(ROOT / "data" / "allnba.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["player", "season"])
        w.writerows(sorted(set(n)))
    print(f"All-NBA selections: {len(set(n))}")
    c = coaches()
    with open(ROOT / "data" / "coaches.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["coach", "team", "first_season", "last_season"])
        w.writerows(c)
    print(f"Coach stints since 2003: {len(c)}")


if __name__ == "__main__":
    main()
