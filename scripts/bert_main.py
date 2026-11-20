"""Step 18: the BERT measure becomes the main measure. Reruns the situation effects and the Step 9 robustness checks on it.

    cd scripts && python bert_main.py        (about 5 minutes)

Main measure (Step 17): share of team-focused pronouns = (team "I" + all "we") / (self "I" + team "I" + all "we") per unit;
conversational "I" is left out. Each "I" is labelled by the Step 17 classifier (data/bert_pronoun_pred.csv); the "we"
classifier failed its bar, so every "we" counts as team.

How: the existing code (models.py, robustness.py, slide_figures.py) is reused unchanged on units whose counts are swapped:
i_count := self "I", we_count := team side. Check: the Step 17 model A result (data/bert_effects.csv) must come out exactly.

Writes data/bert_main_results.txt, data/bert_slide_effects.csv, data/bert_robustness.csv, data/bert_rates.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import models as M
import robustness as RB
import slide_figures as SF

DATA = Path(__file__).resolve().parent.parent / "data"
TIERS = M.TIERS


def bert_units():
    """All model units with the BERT side counts: c_self (self "I"), c_team (team "I" + every "we"), c_neither."""
    idx = pd.read_csv(DATA / "bert_pronoun_index.csv")
    idx["pid"] = np.arange(len(idx))
    pr = pd.read_csv(DATA / "bert_pronoun_pred.csv")
    assert pr[pr.family == "i"].passes.all(), "the \"I\" classifier must pass its bar"
    pr.loc[(pr.family == "we") & ~pr.passes, "label"] = "team"      # a classifier that failed is not used
    idx = idx.merge(pr[["pid", "label"]], on="pid", validate="one_to_one")
    idx["side"] = idx.label.replace({"not_team": "neither"})
    a = pd.read_csv(DATA / "answers_analysis.csv", usecols=["tier", "person_key"])
    a = a[a.tier.isin(TIERS)].reset_index(drop=True)                 # same row numbers as the embedding step
    idx["person_key"] = a.person_key.values[idx.row]
    cnt = (idx.groupby(["interview_id", "person_key", "side"]).size().unstack(fill_value=0)
           .reindex(columns=["self", "team", "neither"], fill_value=0).add_prefix("c_").reset_index())
    u = M.load().merge(cnt, on=["interview_id", "person_key"], how="left")
    u[["c_self", "c_team", "c_neither"]] = u[["c_self", "c_team", "c_neither"]].fillna(0).astype(int)
    assert (u.c_self + u.c_team + u.c_neither == u.i_count + u.we_count).all(), "every counted pronoun has a side"
    return u


def swapped(u):
    """The same units with the counts the existing code reads replaced by the BERT sides."""
    s = u.copy()
    s["i_count_words"], s["we_count_words"] = s.i_count, s.we_count
    s["i_count"], s["we_count"] = s.c_self, s.c_team
    tot = s.i_count + s.we_count
    s["we_share"] = np.where(tot > 0, s.we_count / tot.where(tot > 0), np.nan)
    return s


def main():
    u = bert_units()
    s = swapped(u)
    a = s[(s.i_count + s.we_count) > 0].assign(pron=lambda d: d.i_count + d.we_count)
    lines = ["Step 18: main measure = share of team-focused pronouns (BERT sides), (team \"I\" + all \"we\") / "
             "(self \"I\" + team \"I\" + all \"we\"); conversational \"I\" left out.",
             f"Units with any self- or team-side pronoun: {len(a):,} of {len(s):,}; players {a.person_key.nunique()}", ""]

    # ---- check: reproduce the Step 17 model A result exactly
    res, X = M.fit(a, "we_count", M.LADDER[M.FULL], denom="pron")
    e = M.tier_effects(res, X, "binomial").set_index("tier")
    s17 = pd.read_csv(DATA / "bert_effects.csv")
    s17 = s17[(s17.analysis == "A corrected we-share") & (s17.spec == M.FULL) & (s17.tier == "superstar")].iloc[0]
    assert abs(e.loc["superstar", "diff"] - s17["diff"]) < 1e-9 and abs(e.loc["superstar", "diff_lo"] - s17.diff_lo) < 1e-9, \
        "the swapped units do not reproduce Step 17"
    lines += ["Check: model A on the swapped units reproduces Step 17 exactly: superstar minus role "
              f"{100 * e.loc['superstar', 'diff']:+.2f} pp [{100 * e.loc['superstar', 'diff_lo']:+.2f}, {100 * e.loc['superstar', 'diff_hi']:+.2f}]",
              "Adjusted share by tier (all controls): " + ", ".join(
                  f"{t} {e.loc[t, 'estimate']:.3f} [{e.loc[t, 'lo']:.3f}, {e.loc[t, 'hi']:.3f}]" for t in TIERS), ""]

    # ---- descriptives
    sd = a.we_share.std()
    gd = a[a.game_day == 1]
    pooled = {w: gd[gd.won == w].we_count.sum() / gd[gd.won == w].pron.sum() for w in (0, 1)}
    lines += [f"Unit share: mean {a.we_share.mean():.3f}, SD {sd:.3f} ({100 * sd:.1f} points) over {len(a):,} units",
              f"Pooled game-day share: after losses {pooled[0]:.3f}, after wins {pooled[1]:.3f}",
              "Raw unit means by tier: " + ", ".join(f"{t} {a[a.tier == t].we_share.mean():.3f}" for t in TIERS), ""]

    # ---- situation effects (same five as the slide), model A with all controls
    se, _ = SF.situation_effects(u=s, out=DATA / "bert_slide_effects.csv")
    lines += ["Situation effects (average marginal effects, percentage points of the share, 95% CI):"]
    lines += [f"   {x.effect:<40} {100 * x['diff']:+.1f} [{100 * x.lo:+.1f}, {100 * x.hi:+.1f}]  (n {x.n})" for _, x in se.iterrows()]
    lines.append("")

    # ---- robustness: the same 14 checks as Step 9, plus the plain we-share as the alternative measure
    rb, top10, inter = RB.checks(s)
    w = u.loc[a.index].assign(pron=lambda d: d.i_count + d.we_count)       # same units, counting words
    alt = RB.run_check("Counting words instead (the plain we-share)", w, M.LADDER[M.FULL], group="Measure")
    rb = pd.concat([rb.iloc[:1], pd.DataFrame([alt]), rb.iloc[1:]], ignore_index=True)
    rb.to_csv(DATA / "bert_robustness.csv", index=False)
    lines += ["Robustness (superstar minus role, model A all controls unless noted):",
              f"10 most-interviewed players: {', '.join(top10)}"]
    for _, x in rb.iterrows():
        lvl = "" if np.isnan(x.role) else f"role/rest {x.role:.3f}, superstar {x.superstar:.3f}; "
        lines.append(f"[{x.group}] {x.check}: units {x.n_units}, players {x.n_players}; {lvl}"
                     f"diff {100 * x['diff']:+.1f} pp [{100 * x.diff_lo:+.1f}, {100 * x.diff_hi:+.1f}], p = {x.p:.3f}"
                     + (f"; constant controls dropped: {x.dropped}" if x.dropped else ""))
    checks = rb[~rb.group.isin(["Main", "Measure"])]
    zero_in = int(((checks.diff_lo < 0) & (checks.diff_hi > 0)).sum())
    lines += [f"Checks that include zero: {zero_in} of {len(checks)} (the plain we-share row not counted)", "",
              "Follow-up: one model with tier x game day"] + inter + [""]

    # ---- secondary: rates per 1,000 words (Poisson, offset log words), all units
    rates = []
    for y, label in [("i_count", "self \"I\" per 1,000 words"), ("we_count", "team side per 1,000 words")]:
        res, X = M.fit(s, y, M.LADDER[M.FULL], family="poisson")
        r = M.tier_effects(res, X, "poisson")
        r.insert(0, "measure", label)
        rates.append(r)
        sup = r.set_index("tier").loc["superstar"]
        lines.append(f"Poisson, {label}: " + ", ".join(f"{x.tier} {x.estimate:.1f}" for _, x in r.iterrows())
                     + f"; superstar / role rate ratio {sup.ratio:.2f} [{sup.ratio_lo:.2f}, {sup.ratio_hi:.2f}], p = {sup.p:.3f}")
    pd.concat(rates).to_csv(DATA / "bert_rates.csv", index=False)

    txt = "\n".join(lines) + "\n"
    (DATA / "bert_main_results.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
