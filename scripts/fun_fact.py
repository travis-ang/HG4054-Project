"""Fun fact for the end of the talk (18 Nov, Travis's request): which players have the highest and lowest
team-focused share? Descriptive only; nothing is refitted except one model A fit used for the adjusted ranking.

    cd scripts && python fun_fact.py        (about 3 minutes; needs the Step 17/18 outputs)

Per player, pooled over all their press-conference units (model sample, 4,415 units with a self- or team-side pronoun):
  share    = (team "I" + all "we") / (self "I" + team "I" + all "we")       (the main measure, Step 18)
  95% CI   = Wilson interval on the pooled counts (ignores clustering within a player, so it is too narrow)
  adjusted = observed share minus the share model A (all controls) predicts for the same units, i.e. how far above or
             below the situation (wins, points, minutes, round, question wording and topics) the player sits.
Players need at least MIN_PRON self+team pronouns AND MIN_UNITS units. Rankings are also shown at other cut-offs to
check that the top and bottom names are stable.

Writes data/fun_fact.txt and data/fun_fact.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import bert_main as BM
import models as M

DATA = Path(__file__).resolve().parent.parent / "data"
MIN_PRON, MIN_UNITS = 500, 10
CHECKS = [(200, 5), (500, 10), (1000, 20)]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def players(a):
    g = a.groupby("person_key")
    t = pd.DataFrame({
        "person": g.person.agg(lambda s: s.mode().iloc[0]),
        "player_id": g.player_id.agg(lambda s: int(s.dropna().mode().iloc[0])),
        "units": g.size(),
        "team": g.we_count.sum(),
        "self": g.i_count.sum(),
        "expected_team": g.expected_team.sum(),
        "tiers": g.tier.agg(lambda s: "/".join(sorted(s.unique(), key=M.TIERS.index))),
        "first": g.season.min(), "last": g.season.max(),
    })
    t["pron"] = t.team + t.self
    t["share"] = t.team / t.pron
    t["lo"], t["hi"] = wilson(t.team, t.pron)
    t["adjusted"] = (t.team - t.expected_team) / t.pron
    return t.sort_values("share", ascending=False)


def fmt(r):
    return (f"{r.person:<26} {r.share * 100:5.1f}%  [{r.lo * 100:4.1f}, {r.hi * 100:4.1f}]  "
            f"adj {r.adjusted * 100:+5.1f}  pron {r.pron:5,}  units {r.units:3}  {r.tiers:<20} {r['first']}-{r['last']}")


def main():
    s = BM.swapped(BM.bert_units())
    a = s[(s.i_count + s.we_count) > 0].assign(pron=lambda d: d.i_count + d.we_count).reset_index(drop=True)
    res, X = M.fit(a, "we_count", M.LADDER[M.FULL], denom="pron")
    a["expected_team"] = res.predict(X) * a.pron
    t = players(a)
    pooled = a.we_count.sum() / a.pron.sum()

    lines = ["Fun fact: highest and lowest team-focused share by player (descriptive; Step 18 main measure)",
             f"Units {len(a):,}, players {len(t)}; pooled share over all units {pooled * 100:.1f}%; "
             f"median player share {t.share.median() * 100:.1f}% (all players).",
             "share = (team \"I\" + all \"we\") / (self \"I\" + team \"I\" + all \"we\"), pooled over the player's units.",
             "CI: Wilson on pooled counts (ignores within-player clustering: too narrow). "
             "adj = observed minus model-A prediction (all controls), in points.", ""]
    for mp, mu in CHECKS:
        e = t[(t.pron >= mp) & (t.units >= mu)]
        lines += [f"== at least {mp} self+team pronouns and {mu} units: {len(e)} players; "
                  f"share range {e.share.min() * 100:.1f}% to {e.share.max() * 100:.1f}%",
                  "-- highest share"] + [fmt(r) for _, r in e.head(5).iterrows()] + \
                 ["-- lowest share"] + [fmt(r) for _, r in e.tail(5).iloc[::-1].iterrows()]
        ea = e.sort_values("adjusted", ascending=False)
        lines += ["-- highest adjusted"] + [fmt(r) for _, r in ea.head(3).iterrows()] + \
                 ["-- lowest adjusted"] + [fmt(r) for _, r in ea.tail(3).iloc[::-1].iterrows()] + [""]

    main_e = t[(t.pron >= MIN_PRON) & (t.units >= MIN_UNITS)]
    out = main_e.reset_index()[["person_key", "person", "player_id", "tiers", "first", "last", "units", "self", "team", "pron",
                                "share", "lo", "hi", "expected_team", "adjusted"]]
    out.to_csv(DATA / "fun_fact.csv", index=False)
    txt = "\n".join(lines)
    (DATA / "fun_fact.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
