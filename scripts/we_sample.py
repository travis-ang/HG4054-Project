"""Step 12: validity check. Does "we" in player answers mean the team?

cd scripts && python we_sample.py sample      -> data/we_sample.csv (30 random "we" uses per tier, one per player)
               python we_sample.py summary     -> data/we_check.txt (after the referent column is filled in)
               python we_sample.py blind       -> data/we_blind.csv + data/we_blind_key.csv (second coder, blind)
               python we_sample.py agree [codes.csv] [coder name]  -> data/we_agreement.txt (default: we_blind.csv, "Travis")

Second coder (added 18 Nov): the first codes in we_sample.csv were made by Claude, not blind to tier. "blind" writes the
same 90 uses in a shuffled order without tier, player, team, season or the first codes, for a second coder (Travis).
Do not open we_sample.csv or we_blind_key.csv while coding. "agree" compares the two sets of codes.

Sampling: for each tier, 30 different players drawn at random (seed 0); for each, one random answer with at least
one "we" word, and one random "we" word in it. The context is the sentence with the "we" word and the sentence
before it. Each use is then read and coded by hand into a referent category (see CODES).
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import fightin_words as F

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
N, SEED = 30, 0
WE = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted(F.WE_WORDS, key=len, reverse=True)) + r")\b",
                re.IGNORECASE)
CODES = {"team": "the player's team (players, or players with coaches and staff)",
         "wider": "a wider group that includes the team (organisation, city and fans, the team over several seasons)",
         "other_group": "a smaller or different group: a pair of teammates, travel companions, the league's players, a generation",
         "generic": "generic or fixed phrase, no clear group (we'll see, as we know)"}


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def sample():
    ans = pd.read_csv(DATA / "answers_analysis.csv")
    ans = ans[ans.tier.isin(["role", "starter", "superstar"]) & (ans.we_count > 0)]
    rng = np.random.default_rng(SEED)
    rows = []
    for tier in ["role", "starter", "superstar"]:
        a = ans[ans.tier == tier]
        for p in rng.choice(a.person_key.unique(), N, replace=False):
            r = a[a.person_key == p].sample(1, random_state=int(rng.integers(1e9))).iloc[0]
            sents = sentences(str(r.answer))
            hits = [(i, m) for i, s in enumerate(sents) for m in WE.finditer(s)]
            if not hits:
                continue
            i, m = hits[rng.integers(len(hits))]
            s = sents[i]
            marked = s[:m.start()] + "[[" + m.group(0) + "]]" + s[m.end():]
            context = (sents[i - 1] + " " if i > 0 else "") + marked
            rows.append(dict(tier=tier, person=r.person, season=r.season, round=r["round"], game_day=r.game_day,
                             team=r.team, interview_id=r.interview_id, turn=r.turn, word=m.group(0).lower(),
                             context=context, referent="", note=""))
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "we_sample.csv", index=False)
    print(out.groupby("tier").size())


def summary():
    s = pd.read_csv(DATA / "we_sample.csv")
    assert s.referent.isin(CODES).all(), s[~s.referent.isin(CODES)]
    t = pd.crosstab(s.tier, s.referent).reindex(columns=list(CODES), fill_value=0)
    t["n"] = t.sum(1)
    t["team_or_wider_%"] = (100 * (t.team + t.wider) / t.n).round(0)
    L = ["Step 12: what does \"we\" refer to? 30 random uses per tier, one per player, read by hand", ""]
    L += [f"  {k}: {v}" for k, v in CODES.items()]
    L += ["", t.to_string(), "", "Not the team (other_group or generic):"]
    for _, r in s[s.referent.isin(["other_group", "generic"])].iterrows():
        L.append(f"  [{r.tier}] {r.person} ({r.season}): {r.referent} - {r.note}")
    txt = "\n".join(L)
    (DATA / "we_check.txt").write_text(txt, encoding="utf-8")
    print(txt)


def blind():
    s = pd.read_csv(DATA / "we_sample.csv")
    ans = pd.read_csv(DATA / "answers_analysis.csv", usecols=["interview_id", "turn", "answer"])
    s = s.merge(ans, on=["interview_id", "turn"], how="left", validate="one_to_one")
    order = np.random.default_rng(1).permutation(len(s))
    out = pd.DataFrame({"id": np.arange(1, len(s) + 1), "context": s.context.values[order],
                        "code": "", "my_note": "", "full_answer": s.answer.values[order]})
    key = pd.DataFrame({"id": out.id, "sample_row": order})
    out.to_csv(DATA / "we_blind.csv", index=False, encoding="utf-8-sig")       # utf-8-sig so Excel shows quotes
    key.to_csv(DATA / "we_blind_key.csv", index=False)
    L = ["How to code data/we_blind.csv (90 uses of \"we\", shuffled; tier and player hidden)", "",
         "Read the context column: the sentence with the marked [[we]] word and the sentence before it.",
         "If it is unclear, read full_answer. Put exactly one of these codes in the code column:", ""]
    L += [f"  {k}: {v}" for k, v in CODES.items()]
    L += ["", "my_note is optional. Do not open we_sample.csv or we_blind_key.csv until you have finished.",
          "Save as CSV with the same name, then run: cd scripts && python we_sample.py agree"]
    (DATA / "we_blind_instructions.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def agree(path=None, coder="Travis"):
    """Compare the first codes (Claude, not blind) with a second coder's codes (columns id, code[, my_note])."""
    from sklearn.metrics import cohen_kappa_score
    path = Path(path) if path else DATA / "we_blind.csv"
    try:
        b = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:                                                 # saved by Excel in the local encoding
        b = pd.read_csv(path, encoding="cp1252")
    if "my_note" not in b:
        b["my_note"] = b.get("note", "")
    b["code"] = b.code.astype(str).str.strip().str.lower()
    bad = b[~b.code.isin(CODES)]
    assert bad.empty, f"rows without a valid code ({', '.join(CODES)}):\n{bad[['id', 'code']]}"
    key = pd.read_csv(DATA / "we_blind_key.csv")
    s = pd.read_csv(DATA / "we_sample.csv").reset_index().rename(columns={"index": "sample_row"})
    m = b[["id", "code", "my_note"]].merge(key, on="id").merge(s, on="sample_row")
    first, second = m.referent, m.code
    team1, team2 = first.isin(["team", "wider"]), second.isin(["team", "wider"])
    L = [f"Step 12 second coder: agreement between Claude (first, not blind) and {coder} (second, blind to tier)", "",
         f"Uses: {len(m)}",
         f"All four codes: agreement {100 * (first == second).mean():.0f}%, Cohen's kappa {cohen_kappa_score(first, second):.2f}",
         f"Team (team or wider) vs not: agreement {100 * (team1 == team2).mean():.0f}%, "
         f"Cohen's kappa {cohen_kappa_score(team1, team2):.2f}", "",
         f"Rows: first coder (Claude); columns: second coder ({coder})",
         pd.crosstab(first, second).to_string(), "",
         "Share of uses that mean the team (team or wider), by tier:"]
    for t in ["role", "starter", "superstar"]:
        k = m.tier == t
        L.append(f"  {t:<10} Claude {team1[k].sum()}/{k.sum()}   {coder} {team2[k].sum()}/{k.sum()}")
    L += ["", "Disagreements:"]
    for _, r in m[first != second].iterrows():
        L.append(f"  id {r.id} [{r.tier}] Claude {r.referent}, {coder} {r.code}: {r.context[:160]}")
    txt = "\n".join(L)
    (DATA / "we_agreement.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    {"sample": sample, "summary": summary, "blind": blind, "agree": agree}[sys.argv[1]](*sys.argv[2:])
