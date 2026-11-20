"""Label every answer's speaker: person name, role (player/coach/staff/other), season, superstar.

Used by notebooks/01_eda_labels.ipynb:  from label_speakers import label
Inputs: data/asap_nba_answers.csv, data/allstars.csv, data/coaches.csv
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Speaker-label variants that the header-based matching cannot merge on its own
ALIASES = {  # keys and values are already-normalised keys (see key())
    "steph curry": "stephen curry", "rip hamilton": "richard hamilton",
    "amare stoudemire": "amar'e stoudemire", "jonathan simmons": "jonathon simmons",
    "stephone castle": "stephon castle", "mo williams": "maurice williams",
    "metta world peace": "ron artest", "matthew dellavedova": "matt dellavedova",
    "ty lue": "tyronn lue", "lu dort": "luguentz dort",
    "cam johnson": "cameron johnson", "enes kanter": "enes freedom", "pat beverley": "patrick beverley",
    "patrick mills": "patty mills", "aaron nembhard": "andrew nembhard", "gregg popvich": "gregg popovich",
}

# Non-players who are not in the coach lists (executives, league officials, media, family, hosts).
# Found by reviewing every "player" with no All-Star selection and many answers (see notebook).
NON_PLAYERS = {
    "adam silver", "david stern", "masai ujiri", "bob myers", "mark cuban", "sam presti",
    "rob pelinka", "koby altman", "stuart scott", "ahmad rashad", "craig sager",
    "draven duncan", "sydney duncan", "jerry buss", "jeanie buss", "micky arison",
    "peter holt", "dan gilbert", "joe lacob", "wyc grousbeck", "pat riley",
}

OTHER_LABEL = re.compile(r"MODERATOR|COMMISSIONER|ANNOUNCER|HOST|PRESIDENT|OWNER|^MR\.? |^MS\.? ", re.I)


def key(name):
    """Normalised join key: ascii, lowercase, no punctuation or Jr/Sr/II/III suffix."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = s.lower().replace("-", " ").replace("’", "'")
    s = re.sub(r"[^a-z' ]", "", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return ALIASES.get(s, ALIASES.get(s.replace("'", ""), s))


REGULAR_SEASON_ROUNDS = {"nba_cup", "regular_season_special"}


def season_of(date_str, rnd):
    """Season = year the season ends. Playoff games belong to their calendar year (the 2020
    bubble playoffs ran into October); Oct-Dec regular-season games belong to the next season."""
    d = pd.to_datetime(date_str, errors="coerce")
    if pd.isna(d):
        return pd.NA
    if rnd in REGULAR_SEASON_ROUNDS and d.month >= 9:
        return d.year + 1
    return d.year


def person_of(speaker, listed):
    """Map an answer's speaker label to a person name, using the transcript header names."""
    lab = re.sub(r"^((HEAD|ASSISTANT)\s+)?(COACH|THE)\s+", "", speaker.upper()).strip()
    lk = key(lab)
    names = [n.strip() for n in listed.split(";") if n.strip()]
    for n in names:
        if key(n) == lk:
            return n
    words = lk.split()
    if words:
        cand = [n for n in names if key(n).split() and key(n).split()[-1] == words[-1]
                and (len(words) == 1 or key(n).split()[0][:3] == words[0][:3])]
        if len(cand) == 1:
            return cand[0]
    return lab.title()


def label(df=None):
    if df is None:
        df = pd.read_csv(ROOT / "data" / "asap_nba_answers.csv", dtype=str, keep_default_na=False)
    df = df.copy()
    df["n_words"] = df["n_words"].astype(int)
    df["season"] = pd.Series([season_of(d, r) for d, r in zip(df["date"], df["round"])],
                             index=df.index).astype("Int64")
    df["person"] = [person_of(s, l) for s, l in zip(df["speaker"], df["listed_speakers"])]
    df["person_key"] = df["person"].map(key)
    # one display name per person: the most common spelling of that key
    display = df.groupby("person_key")["person"].agg(lambda s: s.value_counts().index[0])
    df["person"] = df["person_key"].map(display)

    allstars = pd.read_csv(ROOT / "data" / "allstars.csv")
    allstars["person_key"] = allstars["player"].map(key)
    as_set = set(zip(allstars["person_key"], allstars["season"]))
    as_count = allstars.groupby("person_key").size()

    coaches = pd.read_csv(ROOT / "data" / "coaches.csv")
    coaches["person_key"] = coaches["coach"].map(key)
    first_coach = coaches.groupby("person_key")["first_season"].min()

    coach_labelled = set(df.loc[df["speaker"].str.upper().str.contains(r"^(?:HEAD |ASSISTANT )?COACH"),
                                "person_key"])

    def role(r):
        k, season = r.person_key, r.season
        if OTHER_LABEL.search(r.speaker) or k in NON_PLAYERS:
            return "other"
        if k in first_coach.index and (pd.isna(season) or season >= first_coach[k]):
            return "coach"          # coach (or later executive) from their first coaching season on
        if k in coach_labelled and (r.person_key, season) not in as_set:
            return "coach"
        return "player"

    df["role"] = [role(r) for r in df.itertuples()]
    df["superstar"] = [int(r.role == "player" and (r.person_key, r.season) in as_set)
                       for r in df.itertuples()]
    df["career_allstar_selections"] = df["person_key"].map(as_count).fillna(0).astype(int)
    df["postgame"] = df["session"].isin(["postgame", "postgame_probable"]).astype(int)
    return df
