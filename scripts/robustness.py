"""Step 9: robustness checks of the main result (model A, superstar vs role player we-share).

cd scripts && python robustness.py      (first run also fits LDA with K = 5, a few minutes)

Each check changes one choice and re-fits model A with all controls (binomial, SEs clustered by player).
The headline number is superstar minus role player in adjusted we-share (percentage points, 95% CI).
Two checks were added on 18 Nov after the audit: role players who were never All-Stars, and season fixed effects.

Writes data/robustness.csv, data/robustness.txt, data/unit_topics_k5.csv, data/lda_topics_k5.txt,
figures/robustness.png.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

import models as M

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG = ROOT / "data", ROOT / "figures"
NOGAME = ["r_conf", "r_semis", "r_first"]                         # round only
GAMEDAY = ["won_gd", "pts_gd", "min_gd", "r_conf", "r_semis", "r_first"]   # game_day is constant


# ------------------------------------------------------------------ K = 5 topics
def topics_k5():
    path = DATA / "unit_topics_k5.csv"
    if path.exists():
        return pd.read_csv(path)
    import lda_questions as L
    u = L.load()
    X, vec, _, _ = L.build_matrix(u)
    lda = L.fit(X, 5, 0)
    out = u[["interview_id", "person_key"]].copy()
    out[[f"k5_topic_{i + 1}" for i in range(5)]] = lda.transform(X)
    out.to_csv(path, index=False)
    Xbin = (X > 0).astype(np.int8).tocsc()
    coh, per = L.npmi_coherence(lda, Xbin)
    lines = [f"K = 5 robustness model (seed 0, alpha = eta = 1/K). NPMI coherence {coh:.3f}", ""]
    for i, (t, c) in enumerate(zip(L.top_words(lda, vec.get_feature_names_out(), 15), per)):
        lines.append(f"k5_topic_{i + 1} ({c:+.2f}): {', '.join(t)}")
    (DATA / "lda_topics_k5.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return out


# ------------------------------------------------------------------ fitting
def two_group_effect(res, X):
    """Superstar vs everyone else: average adjusted predictions, delta method."""
    b, V = res.params.values, res.cov_params().values
    vals = {}
    for s in (0.0, 1.0):
        Xs = X.copy()
        Xs["superstar_t"] = s
        p = 1 / (1 + np.exp(-(Xs.values @ b)))
        vals[s] = (p.mean(), (p * (1 - p)) @ Xs.values / len(p))
    d, g = vals[1][0] - vals[0][0], vals[1][1] - vals[0][1]
    se = np.sqrt(g @ V @ g)
    return dict(role=vals[0][0], superstar=vals[1][0], diff=d, diff_lo=d - 1.96 * se, diff_hi=d + 1.96 * se,
                ratio=np.exp(res.params["superstar_t"]), p=res.pvalues["superstar_t"])


def drop_separated(d):
    tot = d.groupby("person_key")[["i_count", "we_count"]].sum()
    ok = tot[(tot.i_count > 0) & (tot.we_count > 0)].index
    return d[d.person_key.isin(ok)]


def run_check(name, d, controls, kind="three", fe=False, group=""):
    d = d.reset_index(drop=True).copy()
    d["cluster"] = d.person_key.astype("category").cat.codes
    if fe:
        d = drop_separated(d).reset_index(drop=True)
        d["cluster"] = d.person_key.astype("category").cat.codes
    dropped = [c for c in controls if d[c].nunique() < 2]          # constant in this subset (e.g. a round with no units)
    controls = [c for c in controls if c not in dropped]
    counts = d.tier.value_counts()
    row = dict(group=group, check=name, dropped=", ".join(dropped), n_units=len(d), n_players=d.person_key.nunique(),
               units_superstar=counts.get("superstar", 0), units_starter=counts.get("starter", 0),
               units_role=counts.get("role", 0))
    if kind == "ols":                               # each unit weighted equally
        X = sm.add_constant(d[["starter", "superstar_t"] + controls].astype(float))
        res = sm.OLS(d.we_share, X).fit(cov_type="cluster", cov_kwds={"groups": d.cluster})
        c, (lo, hi) = res.params["superstar_t"], res.conf_int().loc["superstar_t"]
        row.update(diff=c, diff_lo=lo, diff_hi=hi, p=res.pvalues["superstar_t"],
                   role=np.nan, superstar=np.nan, ratio=np.nan)
        return row
    if kind == "two":
        X = sm.add_constant(d[["superstar_t"] + controls].astype(float))
        if fe:
            X = pd.concat([X, pd.get_dummies(d.person_key, prefix="p", drop_first=True, dtype=float)], axis=1)
        endog = np.column_stack([d.we_count, d.pron - d.we_count])
        res = sm.GLM(endog, X, family=sm.families.Binomial()).fit(
            cov_type="cluster", cov_kwds={"groups": d.cluster}, maxiter=200)
        row.update(two_group_effect(res, X))
        return row
    res, X = M.fit(d, "we_count", controls, fe=fe, denom="pron")
    e = M.tier_effects(res, X, "binomial").set_index("tier")
    s = e.loc["superstar"]
    row.update(role=e.loc["role", "estimate"], superstar=s.estimate, diff=s["diff"], diff_lo=s.diff_lo,
               diff_hi=s.diff_hi, ratio=s.ratio, p=s.p)
    return row


def checks(u):
    a = u[(u.i_count + u.we_count) > 0].assign(pron=lambda d: d.i_count + d.we_count)
    FULL = M.LADDER[M.FULL]
    rows = []
    rows.append(run_check("Main result (model A, all controls)", a, FULL, group="Main"))

    # --- how status is defined
    an = a.copy()
    an["tier"] = np.select([an.allnba == 1, an.start_share >= 0.5, an.start_share < 0.5],
                           ["superstar", "starter", "role"], default="unknown")
    an = an[an.tier != "unknown"]
    an["starter"], an["superstar_t"] = (an.tier == "starter").astype(float), (an.tier == "superstar").astype(float)
    rows.append(run_check("Superstar = All-NBA that season", an, FULL, group="Status definition"))
    rows.append(run_check("All-NBA, same player (fixed effects)", an, FULL, fe=True, group="Status definition"))
    rows.append(run_check("Two groups: superstar vs everyone else", a, FULL, kind="two", group="Status definition"))
    # added 18 Nov after the audit: drop role-player units of players who were All-Stars in any other season
    # (before or after, e.g. Ginobili, Iguodala, Payton, Ray Allen), for whom "role player" is a role, not low status
    from label_speakers import key
    ever = set(pd.read_csv(DATA / "allstars.csv").player.map(key))
    rows.append(run_check("Role players who were never All-Stars", a[~((a.tier == "role") & a.person_key.isin(ever))],
                          FULL, group="Status definition"))

    # --- which press conferences
    rows.append(run_check("Game days only", a[a.game_day == 1], GAMEDAY + ["q_you_rate"] + M.TOPICS,
                          group="Which press conferences"))
    # non-game days exist almost only in the Finals and conference finals (1 semifinal unit, 0 first-round)
    ng = a[(a.game_day == 0) & a["round"].isin(["finals", "conference_finals"])]
    rows.append(run_check("Non-game days only", ng, ["r_conf", "q_you_rate"] + M.TOPICS,
                          group="Which press conferences"))
    rows.append(run_check("Game days, same player (fixed effects)", a[a.game_day == 1],
                          GAMEDAY + ["q_you_rate"] + M.TOPICS, fe=True, group="Which press conferences"))
    rows.append(run_check("Non-game days, same player (fixed effects)", ng, ["r_conf", "q_you_rate"] + M.TOPICS,
                          fe=True, group="Which press conferences"))
    rows.append(run_check("NBA Finals only", a[a["round"] == "finals"],
                          ["game_day", "won_gd", "pts_gd", "min_gd", "q_you_rate"] + M.TOPICS,
                          group="Which press conferences"))

    # --- which players
    rows.append(run_check("Without LeBron James", a[a.person_key != "lebron james"], FULL, group="Which players"))
    top10 = a.person_key.value_counts().head(10).index
    rows.append(run_check("Without the 10 most-interviewed players", a[~a.person_key.isin(top10)], FULL,
                          group="Which players"))

    # --- how the model is set up
    k5 = topics_k5()
    b = a.drop(columns=[c for c in a if c.startswith("topic_")]).merge(k5, on=["interview_id", "person_key"])
    rows.append(run_check("Question topics from LDA with K = 5", b,
                          M.GAME + ["q_you_rate"] + [f"k5_topic_{i}" for i in range(2, 6)], group="Model set-up"))
    rows.append(run_check("Each unit weighted equally (linear model)", a, FULL, kind="ols", group="Model set-up"))
    # added 18 Nov after the audit: era. The superstar share of units and we-share both fall in later seasons,
    # so add a fixed effect for each season on top of all controls
    seasons = pd.get_dummies(a.season, prefix="season", drop_first=True, dtype=float)
    rows.append(run_check("Season fixed effects (era)", pd.concat([a, seasons], axis=1), FULL + list(seasons.columns),
                          group="Model set-up"))
    return pd.DataFrame(rows), top10, interaction(a)


def interaction(a):
    """Follow-up: does the tier gap differ between game days and other days? One model, tier x game_day."""
    # Selection check: a role player may reach the post-game podium only after an unusually good game for him.
    # Points and minutes relative to the player's own average in that season's playoffs (game days only).
    g = pd.read_csv(DATA / "nba_playoff_gamelogs.csv")
    avg = g.groupby(["season", "player_id"])[["pts", "min"]].mean().rename(columns=lambda c: c + "_avg").reset_index()
    a = a.merge(avg, on=["season", "player_id"], how="left")
    gd = a.game_day == 1
    a["pts_rel_gd"] = np.where(gd, a.pts - a.pts_avg, 0.0)
    a["min_rel_gd"] = np.where(gd, a["min"] - a.min_avg, 0.0)
    a[["pts_rel_gd", "min_rel_gd"]] = a[["pts_rel_gd", "min_rel_gd"]].fillna(0.0)
    out = ["Game days: points and minutes above the player's own playoff average that season, mean by tier:"]
    out += ["   " + line for line in a[gd].groupby("tier")[["pts_rel_gd", "min_rel_gd"]].mean().round(2).to_string().split("\n")]
    variants = [("all controls", False, []), ("same player (fixed effects)", True, []),
                ("+ points and minutes relative to own average", False, ["pts_rel_gd", "min_rel_gd"])]
    for name, fe, extra in variants:
        d = (drop_separated(a) if fe else a).reset_index(drop=True).copy()
        d["cluster"] = d.person_key.astype("category").cat.codes
        d["starter_x_gd"], d["super_x_gd"] = d.starter * d.game_day, d.superstar_t * d.game_day
        res, X = M.fit(d, "we_count", M.LADDER[M.FULL] + extra + ["starter_x_gd", "super_x_gd"], fe=fe, denom="pron")
        b, V = res.params, res.cov_params()
        out.append(f"Tier x game day, {name}: units {len(d)}, players {d.person_key.nunique()}")
        for lab, terms in [("superstar vs role, non-game days", ["superstar_t"]),
                           ("superstar vs role, game days", ["superstar_t", "super_x_gd"]),
                           ("difference (interaction)", ["super_x_gd"])]:
            g = np.array([1.0 if c in terms else 0.0 for c in b.index])
            est, se = g @ b.values, np.sqrt(g @ V.values @ g)
            z = est / se
            from scipy.stats import norm
            out.append(f"   {lab:<36} OR {np.exp(est):.2f} [{np.exp(est - 1.96 * se):.2f}, {np.exp(est + 1.96 * se):.2f}], "
                       f"p = {2 * norm.sf(abs(z)):.3f}")
        w = res.wald_test("starter_x_gd = 0, super_x_gd = 0", scalar=True)
        out.append(f"   joint test of both tier x game-day terms: chi2 = {float(w.statistic):.2f}, df = 2, p = {float(w.pvalue):.3f}")
    return out


# ------------------------------------------------------------------ output
def figure(r):
    r = r.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = np.arange(len(r))
    main = r.group == "Main"
    ax.axvline(0, color="#999999", lw=1)
    for yy, (_, row) in zip(y, r.iterrows()):
        col = "#2a78d6"
        ax.plot([100 * row.diff_lo, 100 * row.diff_hi], [yy, yy], color=col, lw=2, solid_capstyle="round")
        ax.scatter(100 * row["diff"], yy, s=70 if row.group == "Main" else 50, color=col, edgecolor="white",
                   linewidth=1.5, zorder=3)
        ax.text(100 * row.diff_hi + 0.4, yy, f"{100 * row['diff']:+.1f} [{100 * row.diff_lo:+.1f}, {100 * row.diff_hi:+.1f}]",
                va="center", fontsize=8, color="#444444")
    ax.set_yticks(y, [("$\\bf{" + c.replace(" ", "\\ ").replace(",", "{,}") + "}$") if m else c
                      for c, m in zip(r.check, main)])
    ax.set_xlabel("Superstar minus role player, adjusted we-share (percentage points)")
    for i in range(1, len(r)):
        if r.group[i] != r.group[i - 1]:
            ax.axhline(i - 0.5, color="#e6e6e6", lw=0.8)
    lim = max(abs(100 * r.diff_lo.min()), abs(100 * r.diff_hi.max())) + 4
    ax.set_xlim(-lim, lim + 4)                     # room for the value labels on the right
    ax.grid(axis="x", color="#eeeeee", lw=0.8)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.suptitle("The superstar - role player gap under each robustness check", x=0.01, ha="left", y=0.98, fontsize=13)
    fig.text(0.01, 0.01, "Dots: difference in average predicted we-share. Bars: 95% CI, SEs clustered by player. "
             "'Two groups' compares superstars with everyone else.", fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "robustness.png", dpi=200)
    plt.close(fig)


def main():
    u = M.load()
    r, top10, inter = checks(u)
    r.to_csv(DATA / "robustness.csv", index=False)
    lines = ["Step 9 robustness. Superstar minus role player in adjusted we-share (model A, all controls unless noted).",
             f"10 most-interviewed players: {', '.join(top10)}", ""]
    for _, x in r.iterrows():
        lines.append(f"[{x.group}] {x.check}")
        lines.append(f"   units {x.n_units} (superstar {x.units_superstar}, starter {x.units_starter}, role {x.units_role}), "
                     f"players {x.n_players}" + (f"; constant controls dropped: {x.dropped}" if x.dropped else ""))
        lvl = "" if np.isnan(x.role) else f"role/rest {x.role:.3f}, superstar {x.superstar:.3f}; "
        orr = "" if np.isnan(x.ratio) else f", OR {x.ratio:.2f}"
        lines.append(f"   {lvl}diff {100 * x['diff']:+.1f} pp [{100 * x.diff_lo:+.1f}, {100 * x.diff_hi:+.1f}]{orr}, p = {x.p:.3f}")
    lines += ["", "Follow-up (added after the game-day check): one model with tier x game day"] + inter
    txt = "\n".join(lines) + "\n"
    (DATA / "robustness.txt").write_text(txt, encoding="utf-8")
    print(txt)
    figure(r)


if __name__ == "__main__":
    main()
