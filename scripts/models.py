"""Step 8: regression models of self-focus by status tier.

cd scripts && python models.py

Main measure: we-share = we / (I + we) per unit (one player in one press conference).
  A  binomial (logistic) regression of we-share on tier + controls, SEs clustered by player.
     Fitted as a ladder: tier only -> + game and round -> + question "you" rate -> + question topics.
  B  A (full controls) + player fixed effects: same player, star vs non-star seasons.
  C  Poisson regressions of the I and we counts, offset log(words).
Secondary (exploratory):
  S1 I without hedges ("I think", "I mean", "I don't know", "I guess"): A and C re-run.
  S2 teammate credit: teammate names + team words, Poisson with offset log(words).

Writes data/model_effects.csv, data/model_results.txt, data/teammate_counts.csv,
figures/weshare_by_tier.png, figures/pronoun_rates_by_tier.png.
"""
import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG = ROOT / "data", ROOT / "figures"
TIERS = ["role", "starter", "superstar"]
TIER_NAME = {"role": "Role player", "starter": "Starter", "superstar": "Superstar"}
COLORS = {"role": "#eb6834", "starter": "#1baf7a", "superstar": "#2a78d6"}
TOPICS = [f"topic_{k}" for k in range(2, 11)]          # topic_1 (season and playoff run) is the baseline
GAME = ["game_day", "won_gd", "pts_gd", "min_gd", "r_conf", "r_semis", "r_first"]
LADDER = {                                             # name -> controls
    "1 Tier only": [],
    "2 + game and round": GAME,
    "3 + question 'you' rate": GAME + ["q_you_rate"],
    "4 + question topics": GAME + ["q_you_rate"] + TOPICS,
}
NO_TOPICS, FULL = "3 + question 'you' rate", "4 + question topics"

HEDGES = re.compile(r"\bi (?:think|mean|guess|don'?t know)\b")
TEAM_WORDS = re.compile(r"\b(?:teammates?|together|everybody|group|(?<!you )(?<!those )(?:my|our|the|these) guys)\b")
NICKNAMES = {"Steph": "stephen curry", "Bron": "lebron james", "Melo": "carmelo anthony", "KD": "kevin durant",
             "AD": "anthony davis", "Russ": "russell westbrook", "Manu": "manu ginobili", "Timmy": "tim duncan",
             "Shaq": "shaquille o'neal", "Dray": "draymond green", "JR": "j.r. smith", "CP": "chris paul",
             "Dame": "damian lillard", "Zo": "alonzo mourning", "Sheed": "rasheed wallace", "Boogie": "demarcus cousins"}
SUFFIX = {"jr", "sr", "ii", "iii", "iv"}
AMBIGUOUS = {"West", "White", "Jordan", "Magic", "Bird"}   # usually a direction, a colour or a legend, not a teammate


def fold(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()


# ------------------------------------------------------------------ data
def name_tokens(name):
    toks = [t.strip(".") for t in re.split(r"[\s-]+", fold(name))]
    out = {t for t in toks if len(t) >= 3 and t.lower() not in SUFFIX}
    out |= {nick for nick, full in NICKNAMES.items() if fold(full).lower() == fold(name).lower()}
    return out


def rosters():
    g = pd.read_csv(DATA / "nba_playoff_gamelogs.csv")
    s = pd.read_csv(DATA / "nba_season_starts.csv")
    team_of = g.drop_duplicates(["season", "player_id"]).set_index(["season", "player_id"]).team.to_dict()
    members = pd.concat([g[["season", "team", "player_id", "player"]],
                         s[["season", "team", "player_id", "player"]]]).drop_duplicates(["season", "team", "player_id"])
    roster = {k: list(zip(d.player_id, d.player)) for k, d in members.groupby(["season", "team"])}
    g["opp"] = g.matchup.str[-3:]
    opps = g.groupby(["season", "team"]).opp.agg(set).to_dict()
    return team_of, roster, opps


def teammate_counts(ans):
    """Per answer and per question: mentions of the speaker's teammates' names (case-sensitive; opponents',
    the speaker's own and ambiguous names excluded) and team words."""
    team_of, roster, opps = rosters()
    lower = re.findall(r"\b[a-z]+\b", " ".join(ans.answer.map(fold)))
    common = {w for w, n in pd.Series(lower).value_counts().items() if n >= 20}   # "Love", "Green", "Will"
    cache = {}

    def mates(season, pid):
        key = (season, pid)
        if key not in cache:
            team = team_of.get(key)
            if team is None:
                cache[key] = None
            else:
                own = next((n for p, n in roster[(season, team)] if p == pid), "")
                m = set().union(*[name_tokens(n) for p, n in roster[(season, team)] if p != pid])
                opp = set().union(*[name_tokens(n) for o in opps.get((season, team), ())
                                    for _, n in roster.get((season, o), [])])
                cache[key] = m - opp - name_tokens(own) - AMBIGUOUS
        return cache[key]

    def n_names(text, toks):
        n = 0
        for m in re.finditer(r"[A-Za-z][A-Za-z']*", text):
            w = m.group().removesuffix("'s")
            if w in toks:
                start = re.search(r"(^|[.!?]\s+|\"\s*)$", text[:m.start()]) is not None
                if not (start and w.lower() in common):
                    n += 1
        return n

    out = {k: [] for k in ["mate_names", "team_words", "q_mate_names", "q_team_words", "has_roster"]}
    for season, pid, a, q in zip(ans.season, ans.player_id, ans.answer, ans.question.fillna("")):
        toks = mates(season, pid)
        a, q = fold(a), fold(q)
        out["has_roster"].append(toks is not None)
        out["mate_names"].append(n_names(a, toks) if toks else 0)
        out["q_mate_names"].append(n_names(q, toks) if toks else 0)
        out["team_words"].append(len(TEAM_WORDS.findall(a.lower().replace("’", "'"))))
        out["q_team_words"].append(len(TEAM_WORDS.findall(q.lower().replace("’", "'"))))
    return {k: np.array(v) for k, v in out.items()}


def load():
    u = pd.read_csv(DATA / "units.csv")
    u = u[u.tier.isin(TIERS)].merge(pd.read_csv(DATA / "unit_topics.csv"), on=["interview_id", "person_key"])
    ans = pd.read_csv(DATA / "answers_analysis.csv")
    ans = ans[ans.tier.isin(TIERS)].copy()
    ans["hedges"] = ans.answer.str.lower().str.replace("’", "'").str.count(HEDGES)
    for k, v in teammate_counts(ans).items():
        ans[k] = v
    agg = ans.groupby(["interview_id", "person_key"]).agg(
        hedges=("hedges", "sum"), mate_names=("mate_names", "sum"), team_words=("team_words", "sum"),
        q_mate_names=("q_mate_names", "sum"), q_team_words=("q_team_words", "sum"), has_roster=("has_roster", "all"))
    agg.reset_index().to_csv(DATA / "teammate_counts.csv", index=False)
    u = u.merge(agg.reset_index(), on=["interview_id", "person_key"])
    gd = u.game_day == 1
    for c in ["won", "pts", "min"]:
        u[f"{c}_gd"] = np.where(gd, u[c], 0.0)
    u["r_conf"] = (u["round"] == "conference_finals").astype(float)
    u["r_semis"] = (u["round"] == "conference_semifinals").astype(float)
    u["r_first"] = (u["round"] == "first_round").astype(float)
    u["starter"] = (u.tier == "starter").astype(float)
    u["superstar_t"] = (u.tier == "superstar").astype(float)
    u["i_nohedge"] = u.i_count - u.hedges
    u["mate_total"] = u.mate_names + u.team_words
    q = u.q_words.replace(0, np.nan)
    u["q_mate_rate"] = 1000 * (u.q_mate_names + u.q_team_words) / q     # the question already names a teammate
    u["cluster"] = u.person_key.astype("category").cat.codes
    return u.reset_index(drop=True)


# ------------------------------------------------------------------ models
def design(u, controls, fe=False):
    X = u[["starter", "superstar_t"] + controls].astype(float)
    if fe:
        X = pd.concat([X, pd.get_dummies(u.person_key, prefix="p", drop_first=True, dtype=float)], axis=1)
    return sm.add_constant(X)


def fit(u, y, controls, family="binomial", fe=False, denom=None):
    X = design(u, controls, fe)
    if family == "binomial":
        endog = np.column_stack([u[y], u[denom] - u[y]])
        model = sm.GLM(endog, X, family=sm.families.Binomial())
    else:
        model = sm.GLM(u[y], X, family=sm.families.Poisson(), offset=np.log(u.words))
    return model.fit(cov_type="cluster", cov_kwds={"groups": u.cluster}, maxiter=200), X


def tier_effects(res, X, family):
    """Average adjusted prediction per tier (everyone set to that tier), and differences from role, delta method."""
    b, V = res.params.values, res.cov_params().values
    out = {}
    for t in TIERS:
        Xt = X.copy()
        Xt["starter"], Xt["superstar_t"] = float(t == "starter"), float(t == "superstar")
        eta = Xt.values @ b
        if family == "binomial":
            p = 1 / (1 + np.exp(-eta))
            val, grad = p.mean(), (p * (1 - p)) @ Xt.values / len(p)
        else:                       # rate per 1,000 words
            r = 1000 * np.exp(eta)
            val, grad = r.mean(), r @ Xt.values / len(r)
        out[t] = (val, grad)
    rows = []
    for t in TIERS:
        val, grad = out[t]
        se = np.sqrt(grad @ V @ grad)
        row = dict(tier=t, estimate=val, lo=val - 1.96 * se, hi=val + 1.96 * se)
        if t != "role":
            d, gd = val - out["role"][0], grad - out["role"][1]
            dse = np.sqrt(gd @ V @ gd)
            coef = res.params["starter" if t == "starter" else "superstar_t"]
            cse = res.bse["starter" if t == "starter" else "superstar_t"]
            row.update(diff=d, diff_lo=d - 1.96 * dse, diff_hi=d + 1.96 * dse,
                       ratio=np.exp(coef), ratio_lo=np.exp(coef - 1.96 * cse), ratio_hi=np.exp(coef + 1.96 * cse),
                       p=res.pvalues["starter" if t == "starter" else "superstar_t"])
        rows.append(row)
    return pd.DataFrame(rows)


def run(u):
    effects, lines = [], []

    def record(analysis, spec, res, X, family, data):
        e = tier_effects(res, X, family)
        e.insert(0, "spec", spec)
        e.insert(0, "analysis", analysis)
        e["n_units"], e["n_players"] = len(data), data.person_key.nunique()
        effects.append(e)
        lines.append(f"\n--- {analysis} | {spec} | units {len(data)}, players {data.person_key.nunique()}")
        for _, r in e.iterrows():
            s = f"  {r.tier:<10} {r.estimate:7.3f} [{r.lo:.3f}, {r.hi:.3f}]"
            if r.tier != "role":
                s += (f"   vs role {r['diff']:+.3f} [{r.diff_lo:+.3f}, {r.diff_hi:+.3f}]"
                      f"   {'OR' if family == 'binomial' else 'RR'} {r.ratio:.2f} [{r.ratio_lo:.2f}, {r.ratio_hi:.2f}]  p={r.p:.3f}")
            lines.append(s)
        return res

    a = u[(u.i_count + u.we_count) > 0].assign(pron=lambda d: d.i_count + d.we_count)
    for spec, ctrl in LADDER.items():
        res, X = fit(a, "we_count", ctrl, denom="pron")
        record("A we-share", spec, res, X, "binomial", a)
        if spec == FULL:
            lines.append("  controls (log-odds, clustered SE):")
            for c in ["q_you_rate", "game_day", "won_gd", "pts_gd", "min_gd", "r_conf", "r_semis", "r_first"]:
                lines.append(f"    {c:<11} {res.params[c]:+.4f}  [{res.conf_int().loc[c, 0]:+.4f}, {res.conf_int().loc[c, 1]:+.4f}]  p={res.pvalues[c]:.3f}")

    # B: same player. Players need units in more than one tier to inform the tier estimate.
    changers = a.groupby("person_key").tier.nunique()
    changers = set(changers[changers > 1].index)
    tot = a.groupby("person_key")[["i_count", "we_count"]].sum()
    ok = set(tot[(tot.i_count > 0) & (tot.we_count > 0)].index)      # all-I or all-we players are perfectly separated
    b = a[a.person_key.isin(ok)]
    res, X = fit(b, "we_count", LADDER[FULL], fe=True, denom="pron")
    record("B same player (FE)", FULL, res, X, "binomial", b)
    lines.append(f"  players who change tier: {len(changers & ok)}, their units: {b.person_key.isin(changers).sum()}")

    for y, label in [("i_count", "C I rate"), ("we_count", "C we rate")]:
        for spec in ["1 Tier only", NO_TOPICS, FULL]:
            res, X = fit(u, y, LADDER[spec], family="poisson")
            record(label, spec, res, X, "poisson", u)

    s1 = u[(u.i_nohedge + u.we_count) > 0].assign(pron=lambda d: d.i_nohedge + d.we_count)
    for spec in ["1 Tier only", NO_TOPICS, FULL]:
        res, X = fit(s1, "we_count", LADDER[spec], denom="pron")
        record("S1 we-share, hedges removed", spec, res, X, "binomial", s1)
        res, X = fit(u, "i_nohedge", LADDER[spec], family="poisson")
        record("S1 I rate, hedges removed", spec, res, X, "poisson", u)

    s2 = u[u.has_roster]
    s2_specs = {"1 Tier only": [], NO_TOPICS: LADDER[NO_TOPICS], FULL: LADDER[FULL],
                "5 + question names a teammate": LADDER[FULL] + ["q_mate_rate"]}
    for y, label in [("mate_total", "S2 teammate credit (total)"), ("mate_names", "S2 teammate names"),
                     ("team_words", "S2 team words")]:
        for spec, ctrl in s2_specs.items():
            res, X = fit(s2, y, ctrl, family="poisson")
            record(label, spec, res, X, "poisson", s2)
        d = s2[s2.groupby("person_key")[y].transform("sum") > 0]       # players who never say it add nothing within-player
        res, X = fit(d, y, s2_specs["5 + question names a teammate"], family="poisson", fe=True)
        record(label, "6 same player (FE)", res, X, "poisson", d)
    return pd.concat(effects, ignore_index=True), lines


# ------------------------------------------------------------------ figures
def style(ax):
    ax.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#999999")
    ax.spines["bottom"].set_color("#999999")
    ax.tick_params(colors="#444444")


def dot_panel(ax, e, specs, labels):
    off = {"role": -0.22, "starter": 0.0, "superstar": 0.22}
    for i, spec in enumerate(specs):
        for t in TIERS:
            r = e[(e.spec == spec) & (e.tier == t)].iloc[0]
            ax.errorbar(i + off[t], r.estimate, yerr=[[r.estimate - r.lo], [r.hi - r.estimate]], fmt="o", ms=8,
                        color=COLORS[t], ecolor=COLORS[t], elinewidth=2, capsize=0,
                        mec="white", mew=1.5, label=TIER_NAME[t] if i == 0 else None)
    ax.set_xticks(range(len(specs)), labels)
    style(ax)


def figures(e):
    FIG.mkdir(exist_ok=True)
    a = e[e.analysis == "A we-share"]
    bfe = e[e.analysis == "B same player (FE)"].assign(spec="B")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    dot_panel(ax, pd.concat([a, bfe]), list(LADDER) + ["B"],
              ["Tier only", "+ game\nand round", "+ question\n'you' rate", "+ question\ntopics", "Same player\n(fixed effects)"])
    ax.axvline(3.5, color="#cccccc", lw=1, ls="--")
    ax.set_ylabel("Adjusted we-share  (we / (I + we))")
    fig.legend(loc="upper right", ncol=3, frameon=False, bbox_to_anchor=(0.98, 0.98))
    fig.suptitle("We-share by tier, as controls are added", x=0.07, ha="left", y=0.96, fontsize=13)
    fig.text(0.07, 0.01, "Dots: average predicted we-share with every unit set to that tier. Bars: 95% CI, SEs clustered by player.",
             fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    fig.savefig(FIG / "weshare_by_tier.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=False)
    for ax, (an, title) in zip(axes, [("C I rate", "\"I\" words per 1,000 words"), ("C we rate", "\"We\" words per 1,000 words")]):
        dot_panel(ax, e[e.analysis == an], ["1 Tier only", NO_TOPICS, FULL], ["Tier only", "+ game, round,\n'you' rate", "+ question\ntopics"])
        ax.set_title(title, loc="left", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=3, frameon=False, bbox_to_anchor=(0.98, 0.98))
    fig.suptitle("Pronoun rates by tier (Poisson, offset log words)", x=0.06, ha="left", y=0.96, fontsize=13)
    fig.text(0.06, 0.01, "Adjusted rates with 95% CIs, SEs clustered by player.", fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    fig.savefig(FIG / "pronoun_rates_by_tier.png", dpi=200)
    plt.close(fig)


def main():
    u = load()
    e, lines = run(u)
    e.to_csv(DATA / "model_effects.csv", index=False)
    head = [f"Step 8 models. Units: {len(u)} ({u.tier.value_counts().to_dict()}), players: {u.person_key.nunique()}.",
            f"Hedges removed from I: {u.hedges.sum()} of {u.i_count.sum()} I words ({u.hedges.sum() / u.i_count.sum():.1%}).",
            f"Teammate names: {u.mate_names.sum()}, team words: {u.team_words.sum()}; units with a roster: {u.has_roster.mean():.1%}.",
            f"Questions: teammate names {u.q_mate_names.sum()}, team words {u.q_team_words.sum()}.",
            "Game days, pooled we-share by result: "
            + ", ".join(f"{'won' if w else 'lost'} {d.we_count.sum() / (d.we_count.sum() + d.i_count.sum()):.3f}"
                        for w, d in u[u.game_day == 1].groupby("won")),
            "Raw medians by tier:",
            u.groupby("tier")[["we_share", "i_rate", "we_rate"]].median().round(3).to_string()]
    (DATA / "model_results.txt").write_text("\n".join(head + lines) + "\n", encoding="utf-8")
    print("\n".join(head + lines))
    figures(e)


if __name__ == "__main__":
    main()
