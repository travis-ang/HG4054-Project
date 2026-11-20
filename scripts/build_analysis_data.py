"""Build the analysis tables: player answers with status tiers and game controls.

python scripts/build_analysis_data.py

Inputs : data/asap_nba_answers.csv, data/allstars.csv, data/allnba.csv, data/coaches.csv,
         data/nba_playoff_gamelogs.csv, data/nba_season_starts.csv
Outputs: data/answers_analysis.csv   one row per player answer (playoffs only)
         data/units.csv              one row per player per press conference (the analysis unit)
         data/match_report.txt       how many speakers/answers matched the official NBA records

Definitions (agreed plan, 8 Nov 2026)
  tier       superstar = All-Star that season
             starter   = not an All-Star, started >= 50% of regular-season games played
             role      = not an All-Star, started <  50% of regular-season games played
  allnba     All-NBA (1st/2nd/3rd team) that season: robustness definition of superstar
  game_day   1 if the player's team played a playoff game on the transcript date (postgame)
  won, pts, min   that game's result and the player's points and minutes (game days only)
  we_share   we / (I + we) first-person pronouns
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from label_speakers import key, label

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
PLAYOFF_ROUNDS = {"finals", "conference_finals", "conference_semifinals", "first_round"}

I_WORDS = {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"}
WE_WORDS = {"we", "us", "our", "ours", "ourselves", "we're", "we've", "we'll", "we'd"}
YOU_WORDS = {"you", "your", "yours", "yourself", "yourselves", "you're", "you've", "you'll", "you'd"}


def tokens(s):
    return re.findall(r"[a-z']+", s.lower().replace("’", "'"))


def counts(s):
    t = tokens(s)
    return len(t), sum(w in I_WORDS for w in t), sum(w in WE_WORDS for w in t), sum(w in YOU_WORDS for w in t)


def main():
    df = label()
    df = df[(df.role == "player") & df["round"].isin(PLAYOFF_ROUNDS)].copy()

    # --- text features -------------------------------------------------------
    a = np.array([counts(s)[:3] for s in df.answer])
    df["words"], df["i_count"], df["we_count"] = a[:, 0], a[:, 1], a[:, 2]
    q = np.array([counts(s) for s in df.question])
    df["q_words"], df["q_you_count"] = q[:, 0], q[:, 3]

    # --- official NBA records ------------------------------------------------
    starts = pd.read_csv(D / "nba_season_starts.csv")
    starts["person_key"] = starts.player.map(key)
    logs = pd.read_csv(D / "nba_playoff_gamelogs.csv")
    logs["person_key"] = logs.player.map(key)
    logs["game_date"] = pd.to_datetime(logs.game_date).dt.normalize()

    # player id: match on (name, season) first, then name only
    by_season = starts.drop_duplicates(["person_key", "season"]).set_index(["person_key", "season"])
    by_name = pd.concat([starts, logs]).drop_duplicates("person_key").set_index("person_key")["player_id"]
    df["player_id"] = [by_season["player_id"].get((k, s), by_name.get(k, np.nan))
                       for k, s in zip(df.person_key, df.season)]

    st = starts.drop_duplicates(["player_id", "season"]).set_index(["player_id", "season"])
    gp = [st["gp"].get((p, s), np.nan) for p, s in zip(df.player_id, df.season)]
    gs = [st["gs"].get((p, s), np.nan) for p, s in zip(df.player_id, df.season)]
    df["reg_gp"], df["reg_gs"] = gp, gs
    df["start_share"] = df.reg_gs / df.reg_gp

    allnba = pd.read_csv(D / "allnba.csv")
    an = set(zip(allnba.player.map(key), allnba.season))
    df["allnba"] = [int((k, s) in an) for k, s in zip(df.person_key, df.season)]

    df["tier"] = np.select(
        [df.superstar == 1, df.start_share >= 0.5, df.start_share < 0.5],
        ["superstar", "starter", "role"], default="unknown")

    # game-day controls: the player's own playoff game on the transcript date
    df["date_dt"] = pd.to_datetime(df.date, errors="coerce").dt.normalize()
    g = logs.drop_duplicates(["player_id", "game_date"]).set_index(["player_id", "game_date"])
    keyidx = list(zip(df.player_id, df.date_dt))
    df["game_day"] = [int(k in g.index) for k in keyidx]
    df["team"] = [g["team"].get(k, np.nan) for k in keyidx]
    df["won"] = [{"W": 1, "L": 0}.get(g["wl"].get(k), np.nan) for k in keyidx]
    df["pts"] = [g["pts"].get(k, np.nan) for k in keyidx]
    df["min"] = [g["min"].get(k, np.nan) for k in keyidx]

    keep = ["interview_id", "turn", "season", "date", "round", "session", "game_day", "person",
            "person_key", "player_id", "team", "tier", "superstar", "allnba", "reg_gp", "reg_gs",
            "start_share", "career_allstar_selections", "won", "pts", "min", "question", "answer",
            "words", "i_count", "we_count", "q_words", "q_you_count", "url"]
    df[keep].to_csv(D / "answers_analysis.csv", index=False)

    # --- analysis unit: one player in one press conference ---------------------
    first = {c: (c, "first") for c in ["season", "date", "round", "session", "game_day", "person",
                                       "player_id", "team", "tier", "superstar", "allnba",
                                       "start_share", "won", "pts", "min", "url"]}
    units = (df.groupby(["interview_id", "person_key"])
             .agg(**first, n_answers=("answer", "size"), words=("words", "sum"),
                  i_count=("i_count", "sum"), we_count=("we_count", "sum"),
                  q_words=("q_words", "sum"), q_you_count=("q_you_count", "sum"),
                  questions=("question", lambda s: " ".join(x for x in s if x)))
             .reset_index())
    units["we_share"] = units.we_count / (units.i_count + units.we_count).replace(0, np.nan)
    units["i_rate"] = 1000 * units.i_count / units.words.replace(0, np.nan)
    units["we_rate"] = 1000 * units.we_count / units.words.replace(0, np.nan)
    units["q_you_rate"] = 1000 * units.q_you_count / units.q_words.replace(0, np.nan)
    units.to_csv(D / "units.csv", index=False)

    # --- report --------------------------------------------------------------
    r = []
    p = r.append
    p(f"Player answers in playoff rounds: {len(df):,}  (players: {df.person_key.nunique()})")
    p(f"Matched to an NBA player id: {df.player_id.notna().mean():.1%} of answers")
    p(f"Have regular-season starts (tier known): {(df.tier != 'unknown').mean():.1%} of answers")
    p(f"Game-day answers (team played that day): {df.game_day.sum():,} "
      f"({df.game_day.mean():.1%}); of ASAP 'postgame' answers matched to a game: "
      f"{df.loc[df.session.isin(['postgame', 'postgame_probable']), 'game_day'].mean():.1%}")
    p("\nAnswers / players by tier:")
    p(df.groupby("tier").agg(answers=("answer", "size"), players=("person_key", "nunique")).to_string())
    p("\nUnits (player x press conference) by tier and game day:")
    p(units.groupby(["tier", "game_day"]).size().unstack(fill_value=0).to_string())
    p("\nUnmatched speakers with most answers (no NBA id or no starts):")
    um = df[df.tier == "unknown"].groupby("person").size().sort_values(ascending=False).head(25)
    p(um.to_string())
    (D / "match_report.txt").write_text("\n".join(r), encoding="utf-8")
    print("\n".join(r))


if __name__ == "__main__":
    main()
