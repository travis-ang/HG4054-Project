"""What reporters ask each tier (18 Nov, Step 21; descriptive): the Step 7 LDA topic shares of the reporters' questions,
superstar vs role player, with 95% CIs clustered by player.

    cd scripts && python lda_tiers.py        (a few seconds)

Per topic (share of a unit's question words on that topic, data/unit_topics.csv, K = 10):
  mean share per tier;
  raw gap      = superstar − role from OLS of the topic share on tier dummies (role baseline), SEs clustered by player;
  adjusted gap = the same with round (Finals baseline) and game day added, because role players are interviewed mostly at
                 the Finals (where some topics are asked more) and less often after games.
A gap "holds" when the adjusted 95% CI excludes zero. Ten tests, no multiple-testing correction: descriptive.
Also reports the share of each tier's units that are at the Finals and on game days.
Writes data/lda_tiers.txt and data/lda_tiers.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

D = Path(__file__).resolve().parent.parent / "data"
TIERS = ["role", "starter", "superstar"]


def gap(d, y, controls):
    X = pd.DataFrame({"starter": (d.tier == "starter").astype(float), "superstar": (d.tier == "superstar").astype(float)})
    for c in controls:
        X[c] = d[c].astype(float)
    res = sm.OLS(d[y], sm.add_constant(X)).fit(cov_type="cluster", cov_kwds={"groups": d.cluster})
    b, se = res.params["superstar"], res.bse["superstar"]
    return b, b - 1.96 * se, b + 1.96 * se, res.pvalues["superstar"]


def main():
    u = pd.read_csv(D / "units.csv")
    u = u[u.tier.isin(TIERS)].merge(pd.read_csv(D / "unit_topics.csv"), on=["interview_id", "person_key"])
    u["cluster"] = u.person_key.astype("category").cat.codes
    for r in ["conference_finals", "conference_semifinals", "first_round"]:
        u[f"r_{r}"] = (u["round"] == r).astype(float)
    ctrl = ["r_conference_finals", "r_conference_semifinals", "r_first_round", "game_day"]
    labels = pd.read_csv(D / "topic_labels.csv").set_index("topic").label
    rows = []
    for t in [f"topic_{k}" for k in range(1, 11)]:
        m = u.groupby("tier")[t].mean()
        raw = gap(u, t, [])
        adj = gap(u, t, ctrl)
        rows.append(dict(topic=t, label=labels[t], **{f"mean_{k}": m[k] for k in TIERS},
                         raw=raw[0], raw_lo=raw[1], raw_hi=raw[2], raw_p=raw[3],
                         adj=adj[0], adj_lo=adj[1], adj_hi=adj[2], adj_p=adj[3],
                         holds=bool(adj[1] > 0 or adj[2] < 0)))
    out = pd.DataFrame(rows).sort_values("raw", ascending=False)
    out.to_csv(D / "lda_tiers.csv", index=False)

    finals = u.groupby("tier")["round"].apply(lambda s: (s == "finals").mean())
    gday = u.groupby("tier").game_day.mean()
    lines = ["What reporters ask each tier: LDA topic shares of the questions (K = 10), superstar − role player",
             f"Units {len(u):,}; players {u.person_key.nunique()}; SEs clustered by player; adjusted = + round and game day.",
             "Share of each tier's units at the Finals: " + ", ".join(f"{k} {finals[k]:.2f}" for k in TIERS) +
             "; on game days: " + ", ".join(f"{k} {gday[k]:.2f}" for k in TIERS), "",
             f"{'topic':<34}{'role':>7}{'starter':>8}{'super':>7}   {'raw gap (pp) [95% CI]':<26}{'adjusted gap (pp) [95% CI]':<28}holds"]
    for _, x in out.iterrows():
        lines.append(f"{x.label:<34}{100 * x.mean_role:7.1f}{100 * x.mean_starter:8.1f}{100 * x.mean_superstar:7.1f}   "
                     f"{100 * x.raw:+5.1f} [{100 * x.raw_lo:+5.1f}, {100 * x.raw_hi:+5.1f}]      "
                     f"{100 * x.adj:+5.1f} [{100 * x.adj_lo:+5.1f}, {100 * x.adj_hi:+5.1f}]        {'yes' if x.holds else 'no'}")
    lines.append(f"\n{int(out.holds.sum())} of 10 adjusted gaps exclude zero (10 tests, no correction; descriptive).")
    (D / "lda_tiers.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
