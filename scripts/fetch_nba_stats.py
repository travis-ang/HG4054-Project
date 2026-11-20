"""Fetch official NBA stats (stats.nba.com via nba_api) for 2004-2026.

python scripts/fetch_nba_stats.py

Writes:
  data/nba_playoff_gamelogs.csv   one row per player per playoff game: season, player_id, player,
                                  team, game_id, game_date, matchup, wl, min, pts
  data/nba_season_starts.csv      one row per player per regular season: season, player_id, player,
                                  team, gp, gs, min_per_game
Season = the year the season ends (2016 = 2015-16). Per-season CSVs are cached in data/raw_nba/.
"""
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguegamelog

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_nba"
SEASONS = range(2004, 2027)
DELAY = 2


def season_str(end_year):
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def cached(name, fn):
    path = RAW / name
    if path.exists():
        return pd.read_csv(path)
    for attempt in range(3):
        try:
            time.sleep(DELAY * (attempt + 1))
            df = fn()
            df.to_csv(path, index=False)
            return df
        except Exception as e:  # network hiccups / throttling
            print(f"  retry {attempt + 1} for {name}: {e}")
    raise RuntimeError(f"failed: {name}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    logs, starts = [], []
    for y in SEASONS:
        s = season_str(y)
        g = cached(f"playoff_log_{y}.csv", lambda: leaguegamelog.LeagueGameLog(
            player_or_team_abbreviation="P", season=s, season_type_all_star="Playoffs",
            timeout=60).get_data_frames()[0])
        allp = cached(f"regular_all_{y}.csv", lambda: leaguedashplayerstats.LeagueDashPlayerStats(
            season=s, season_type_all_star="Regular Season", per_mode_detailed="PerGame",
            timeout=60).get_data_frames()[0])
        st = cached(f"regular_starters_{y}.csv", lambda: leaguedashplayerstats.LeagueDashPlayerStats(
            season=s, season_type_all_star="Regular Season", starter_bench_nullable="Starters",
            timeout=60).get_data_frames()[0])

        g = g.rename(columns=str.lower)[["player_id", "player_name", "team_abbreviation", "game_id",
                                         "game_date", "matchup", "wl", "min", "pts"]]
        g.insert(0, "season", y)
        logs.append(g.rename(columns={"player_name": "player", "team_abbreviation": "team"}))

        a = allp.rename(columns=str.lower)[["player_id", "player_name", "team_abbreviation", "gp", "min"]]
        gs = st.rename(columns=str.lower).set_index("player_id")["gp"]
        a["gs"] = a["player_id"].map(gs).fillna(0).astype(int)
        a.insert(0, "season", y)
        starts.append(a.rename(columns={"player_name": "player", "team_abbreviation": "team",
                                        "min": "min_per_game"}))
        print(f"{y}: {len(g)} playoff player-games, {len(a)} regular-season players")

    pd.concat(logs).to_csv(ROOT / "data" / "nba_playoff_gamelogs.csv", index=False)
    pd.concat(starts).to_csv(ROOT / "data" / "nba_season_starts.csv", index=False)
    print("done")


if __name__ == "__main__":
    main()
