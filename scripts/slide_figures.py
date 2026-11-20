"""Step 13: final slide figures, one message per figure, same style throughout.

    cd scripts && python slide_figures.py        (about 1 minute)

Reads the saved results of Steps 7-12; the only refit is model A (all controls), to turn the
situation effects (win, points, question wording, round) into percentage points of we-share,
so they sit on the same scale as the tier gap. Output: figures/slides/*.png (16:9, 200 dpi),
data/slide_effects.csv.

No titles inside the figures: the slide title carries the message. Tiers are labelled directly
on the marks as well as in a legend (the starter aqua is below 3:1 contrast on white).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "figures" / "slides"
TIERS = ["role", "starter", "superstar"]
NAME = {"role": "Role player", "starter": "Starter", "superstar": "Superstar"}
COL = {"role": "#eb6834", "starter": "#1baf7a", "superstar": "#2a78d6"}
LIGHT = {"role": "#f6b89c", "starter": "#94dcc2", "superstar": "#9fc3ef"}
INK, MUTED, GRID = "#222222", "#666666", "#e3e3e3"
W, H = 12, 6.2

plt.rcParams.update({
    "font.family": "Arial", "font.size": 17, "axes.labelsize": 17, "xtick.labelsize": 16, "ytick.labelsize": 16,
    "axes.edgecolor": "#999999", "axes.labelcolor": INK, "xtick.color": "#444444", "ytick.color": "#444444",
    "text.color": INK, "legend.frameon": False, "legend.fontsize": 16, "savefig.dpi": 200,
})


def clean(ax, grid="y"):
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, lw=0.9)
    ax.set_axisbelow(True)


def note(fig, text):
    fig.text(0.012, 0.015, text, fontsize=12, color=MUTED, ha="left", va="bottom")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name)
    plt.close(fig)
    print("wrote", OUT / name)


def pp(x):
    return f"{100 * x:+.1f}".replace("-", "−")


def ci(lo, hi):
    return f"[{pp(lo)}, {pp(hi)}]"


# ------------------------------------------------------------------ data for the refit
def load_units():
    u = pd.read_csv(DATA / "units.csv")
    u = u[u.tier.isin(TIERS)].merge(pd.read_csv(DATA / "unit_topics.csv"), on=["interview_id", "person_key"])
    gd = u.game_day == 1
    for c in ["won", "pts", "min"]:
        u[f"{c}_gd"] = np.where(gd, u[c], 0.0)
    for col, r in [("r_conf", "conference_finals"), ("r_semis", "conference_semifinals"), ("r_first", "first_round")]:
        u[col] = (u["round"] == r).astype(float)
    u["starter"] = (u.tier == "starter").astype(float)
    u["superstar_t"] = (u.tier == "superstar").astype(float)
    u["cluster"] = u.person_key.astype("category").cat.codes
    return u.reset_index(drop=True)


CONTROLS = ["game_day", "won_gd", "pts_gd", "min_gd", "r_conf", "r_semis", "r_first", "q_you_rate"] + \
           [f"topic_{k}" for k in range(2, 11)]


def situation_effects(u=None, out=DATA / "slide_effects.csv"):
    """Average marginal effects (counterfactual change in mean predicted we-share), delta-method CIs.
    u: units to use (default: the we-share units); Step 18 passes units whose counts are the BERT sides."""
    u = load_units() if u is None else u
    u = u[(u.i_count + u.we_count) > 0].reset_index(drop=True)
    X = sm.add_constant(u[["starter", "superstar_t"] + CONTROLS].astype(float))
    y = np.column_stack([u.we_count, u.i_count])
    res = sm.GLM(y, X, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": u.cluster})
    b, V = res.params.values, res.cov_params().values

    def mean_p(Xc):
        p = 1 / (1 + np.exp(-(Xc.values @ b)))
        return p.mean(), (p * (1 - p)) @ Xc.values / len(p)

    def effect(label, rows, set0, set1):
        X0, X1 = X[rows].copy(), X[rows].copy()
        for k, v in set0.items():
            X0[k] = v(X0) if callable(v) else v
        for k, v in set1.items():
            X1[k] = v(X1) if callable(v) else v
        (m0, g0), (m1, g1) = mean_p(X0), mean_p(X1)
        se = np.sqrt((g1 - g0) @ V @ (g1 - g0))
        d = m1 - m0
        return dict(effect=label, diff=d, lo=d - 1.96 * se, hi=d + 1.96 * se, n=int(rows.sum()))

    allr, gd = np.ones(len(u), bool), (u.game_day == 1).values
    rows = [
        effect("Superstar vs role player", allr, {"starter": 0, "superstar_t": 0}, {"starter": 0, "superstar_t": 1}),
        effect("Won vs lost (game days)", gd, {"won_gd": 0}, {"won_gd": 1}),
        effect("+10 points scored (game days)", gd, {}, {"pts_gd": lambda d: d.pts_gd + 10}),
        effect("+10 'you' per 1,000 question words", allr, {}, {"q_you_rate": lambda d: d.q_you_rate + 10}),
        effect("Conference finals vs NBA Finals", allr, {"r_conf": 0, "r_semis": 0, "r_first": 0},
               {"r_conf": 1, "r_semis": 0, "r_first": 0}),
    ]
    e = pd.DataFrame(rows)
    e.to_csv(out, index=False)
    print(e.to_string())
    return e, u


# ------------------------------------------------------------------ figures
def fig_data(u):
    """Slide 3: the data, units per tier split by session."""
    fig, ax = plt.subplots(figsize=(W, 5.2))
    order = ["superstar", "starter", "role"]
    for i, t in enumerate(order):
        d = u[u.tier == t]
        g, o = int((d.game_day == 1).sum()), int((d.game_day == 0).sum())
        ax.barh(i, g, color=COL[t], height=0.62, edgecolor="white", linewidth=2)
        ax.barh(i, o, left=g, color=LIGHT[t], height=0.62, edgecolor="white", linewidth=2)
        ax.text(g / 2, i, f"{g:,}", ha="center", va="center", color="white", fontsize=17, fontweight="bold")
        ax.text(g + o / 2, i, f"{o:,}", ha="center", va="center", color=INK, fontsize=17)
        ax.text(g + o + 40, i, f"{d.person_key.nunique()} players", ha="left", va="center", fontsize=16, color=MUTED)
    ax.set_yticks(range(3), [NAME[t] for t in order], fontsize=18)
    ax.invert_yaxis()
    ax.set_xlim(0, 2300)
    ax.set_xlabel("Press-conference units (one player in one press conference)")
    clean(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(handles=[Patch(color="#555555", label="Darker shade: game day (post-game)"),
                       Patch(color="#c8c8c8", label="Lighter shade: other days (practice, media day)")],
              loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=15)
    note(fig, f"NBA playoff press conferences, ASAP Sports transcripts 2004–2026. {len(u):,} units, "
              f"{u.person_key.nunique()} players (units with reporters' questions,\nas in the models). "
              "Players who changed tier are counted in each tier they appear in.")
    fig.tight_layout(rect=(0, 0.09, 1, 0.95))
    save(fig, "s03_data.png")


def fig_main():
    """Slide 5: adjusted we-share by tier: no controls, all controls, same player."""
    e = pd.read_csv(DATA / "model_effects.csv")
    groups = [("A we-share", "1 Tier only", "No controls"),
              ("A we-share", "4 + question topics", "All controls"),
              ("B same player (FE)", "4 + question topics", "Same player,\nstar vs non-star seasons")]
    off = {"role": -0.2, "starter": 0.0, "superstar": 0.2}
    fig, ax = plt.subplots(figsize=(W, H))
    ax.axhline(0.5, color="#bbbbbb", lw=1.2, ls="--", zorder=0)
    ax.text(2.62, 0.5, "equal\n\"I\" and \"we\"", fontsize=13, color=MUTED, va="center", ha="left")
    for i, (an, spec, _) in enumerate(groups):
        g = e[(e.analysis == an) & (e.spec == spec)].set_index("tier")
        for t in TIERS:
            r = g.loc[t]
            ax.plot([i + off[t]] * 2, [r.lo, r.hi], color=COL[t], lw=3, solid_capstyle="round")
            ax.plot(i + off[t], r.estimate, "o", ms=12, color=COL[t], mec="white", mew=2)
            if i == 0:
                ax.text(i + off[t], r.hi + 0.004, NAME[t].replace(" ", "\n"), ha="center", va="bottom",
                        fontsize=13, color=INK)
        s = g.loc["superstar"]
        ax.text(i, 0.433, f"Superstar − role:\n{pp(s['diff'])} pp {ci(s.diff_lo, s.diff_hi)}",
                ha="center", va="bottom", fontsize=14, color=INK)
    ax.set_xticks(range(3), [x[2] for x in groups], fontsize=17)
    ax.set_xlim(-0.55, 2.95)
    ax.set_ylim(0.43, 0.575)
    ax.set_ylabel("Adjusted we-share   we / (I + we)")
    clean(ax)
    ax.tick_params(axis="x", length=0)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", ms=11, color=COL[t], mec="white", label=NAME[t]) for t in TIERS],
              loc="upper right", ncol=3, bbox_to_anchor=(1.0, 1.06))
    note(fig, "Binomial regression, 4,420 units, 377 players. Dots: average predicted we-share with every unit set to "
              "that tier; bars: 95% CI, SEs clustered by player.\nAll controls: game day, win, points, minutes, round, "
              "'you' in questions, question topics (LDA). Same player: player fixed effects (86 players change tier).")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    save(fig, "s05_main_result.png")


def fig_situation(e):
    """Slide 5/7: what does move we-share (percentage points, same model)."""
    fig, ax = plt.subplots(figsize=(W, 5.6))
    e = e.iloc[::-1].reset_index(drop=True)
    ax.axvline(0, color="#999999", lw=1.2)
    for i, r in e.iterrows():
        status = r.effect.startswith("Superstar")
        c = COL["superstar"] if status else "#444444"
        ax.plot([100 * r.lo, 100 * r.hi], [i, i], color=c, lw=3.5, solid_capstyle="round")
        ax.plot(100 * r["diff"], i, "o", ms=13, color=c, mec="white", mew=2)
        ax.text(100 * max(r.hi, 0) + 0.5, i, f"{pp(r['diff'])} pp {ci(r.lo, r.hi)}", va="center", fontsize=15,
                color=INK, fontweight="bold" if status else "normal")
    ax.set_yticks(range(len(e)), e.effect, fontsize=17)
    for lab in ax.get_yticklabels():
        if lab.get_text().startswith("Superstar"):
            lab.set_fontweight("bold")
    ax.set_xlim(-14, 14)
    ax.set_ylim(-0.6, len(e) - 0.4)
    ax.axhline(len(e) - 1.5, color=GRID, lw=1.2)
    ax.set_xlabel("Change in adjusted we-share (percentage points)")
    clean(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    note(fig, "Same model as the main result (all controls). Average marginal effects with 95% CIs, SEs clustered by "
              "player. Game-day effects averaged over game-day units.\n'You' rate: SD about 21 per 1,000 question words.")
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    save(fig, "s05b_situation.png")


def fig_words(n=12):
    """Slide 6: Fightin' Words, back to back."""
    f = pd.read_csv(DATA / "fightin_words.csv")
    sup = f.sort_values("z", ascending=False).head(n)
    rol = f.sort_values("z").head(n)
    fig, axes = plt.subplots(1, 2, figsize=(W, H), sharex=False)
    for ax, d, t, sign in [(axes[0], rol, "role", -1), (axes[1], sup, "superstar", 1)]:
        d = d.reset_index(drop=True)
        holds = d.mw_p < 0.05
        ax.barh(range(n), d.z.abs(), color=[COL[t] if h else LIGHT[t] for h in holds], height=0.7,
                edgecolor="white", linewidth=1.5)
        ax.set_yticks(range(n), ["I (pronoun)" if w == "i" else w for w in d.word], fontsize=17)
        ax.invert_yaxis()
        ax.set_xlim(0, 12.5)
        ax.set_xticks([0, 4, 8, 12])
        ax.axvline(1.96, color="#999999", lw=1.2, ls="--")
        ax.set_title(f"{NAME[t]}s use more", loc="left", fontsize=18, color=INK, pad=10)
        ax.set_xlabel("|z| (log-odds, Fightin' Words)", fontsize=15)
        clean(ax, "x")
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    fig.legend(handles=[Patch(color="#555555", label="Darker: also holds when each player counts once (p < 0.05)"),
                        Patch(color="#c8c8c8", label="Lighter: pooled answers only")],
               loc="upper right", ncol=2, fontsize=14, bbox_to_anchor=(0.995, 1.0))
    note(fig, "Monroe et al. (2008) log-odds with informative Dirichlet prior; superstar vs role-player answers; names, "
              "teams and cities removed. Dashed line: |z| = 1.96.\nSuperstars also use more of both \"I\" (z = +6.5) "
              "and \"we\" (z = +3.3) words overall, so we-share stays flat. Descriptive, no controls.")
    fig.tight_layout(rect=(0, 0.09, 1, 0.94), w_pad=3)
    save(fig, "s06_words.png")


def fig_classifiers():
    """Slide 6: classifier AUCs on held-out players."""
    r = pd.read_csv(DATA / "classifier_results.csv").set_index("model")
    order = [("E1", "\"I\" and \"we\" rates only"), ("B1", "Session and round only (no words)"),
             ("B2", "Length only (no words)"), ("E3", "Sentence embeddings (MiniLM)"),
             ("E2", "Bag of words"), ("E2b", "Bag of words without \"I\"/\"we\"")]
    fig, ax = plt.subplots(figsize=(W, H))
    c = COL["superstar"]
    ax.axvline(0.5, color="#999999", lw=1.2, ls="--")
    ax.text(0.502, 5.62, "chance", fontsize=13, color=MUTED, va="center")
    for i, (m, lab) in enumerate(order):
        y = 5 - i
        row = r.loc[m]
        ax.plot([row.lo, row.hi], [y + 0.15] * 2, color=c, lw=3.5, solid_capstyle="round")
        ax.plot(row.auc_seed0, y + 0.15, "o", ms=13, color=c, mec="white", mew=2)
        ax.plot([row.len_lo, row.len_hi], [y - 0.17] * 2, color=LIGHT["superstar"], lw=3, solid_capstyle="round")
        ax.plot(row.auc_within_length, y - 0.17, "o", ms=11, mfc="white", mec=c, mew=2.5)
        ax.text(max(row.hi, row.len_hi) + 0.008, y, f"{row.auc_seed0:.2f}  /  {row.auc_within_length:.2f}",
                va="center", fontsize=16, fontweight="bold" if m in ("E1", "E2", "E2b") else "normal")
    ax.set_yticks(range(6), [lab for _, lab in order][::-1], fontsize=17)
    for lab in ax.get_yticklabels():
        if "rates only" in lab.get_text() or lab.get_text().startswith("Bag"):
            lab.set_fontweight("bold")
    ax.set_xlim(0.44, 0.9)
    ax.set_ylim(-0.6, 5.9)
    ax.set_xlabel("AUC on players the model never saw (0.5 = chance, 1 = perfect)")
    clean(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(handles=[Line2D([], [], marker="o", ls="-", lw=3, ms=11, color=c, mec="white", label="All press conferences"),
                       Line2D([], [], marker="o", ls="-", lw=3, ms=10, color=LIGHT["superstar"], mfc="white", mec=c,
                              mew=2.5, label="Compared within similar length")],
              loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=15)
    note(fig, "Superstar (1,917) vs role-player (957) units, 271 players. Logistic regression, 5-fold CV grouped by player; "
              "95% CIs from a player bootstrap.\nSimilar length = AUC within fifths of the word count. Superstars talk more "
              "(median 670 vs 423 words per press conference).")
    fig.tight_layout(rect=(0, 0.09, 1, 0.97))
    save(fig, "s06b_classifiers.png")


def fig_topics(u):
    """Slide 7: what reporters ask about, by tier (LDA, descriptive)."""
    lab = pd.read_csv(DATA / "topic_labels.csv")
    tcols = [f"topic_{k}" for k in range(1, 11)]
    m = u.groupby("tier")[tcols].mean().T
    m["label"] = lab.set_index("topic").loc[tcols, "label"].values
    m["gap"] = m.superstar - m.role
    m = m.sort_values("gap").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(W, H))
    for i, r in m.iterrows():
        lo, hi = min(r[TIERS]), max(r[TIERS])
        ax.plot([100 * lo, 100 * hi], [i, i], color="#d0d0d0", lw=3, zorder=1, solid_capstyle="round")
        for t in TIERS:
            ax.plot(100 * r[t], i, "o", ms=13, color=COL[t], mec="white", mew=2, zorder=2)
    ax.set_yticks(range(len(m)), m.label, fontsize=16)
    ax.set_ylim(-0.6, len(m) - 0.1)
    ax.set_xlabel("Average share of the reporters' questions (%)")
    clean(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", ms=11, color=COL[t], mec="white", label=NAME[t]) for t in TIERS],
              loc="lower left", bbox_to_anchor=(0.0, 1.03), ncol=3, fontsize=15)
    note(fig, f"LDA on the reporters' questions, 10 topics, {len(u):,} units. Sorted by superstar minus role player "
              "(top: asked of superstars more).\nDescriptive; the topics are controls in the main model.")
    fig.tight_layout(rect=(0, 0.09, 1, 0.96))
    save(fig, "s07_topics.png")


def fig_robustness():
    """Slide 7: the superstar - role gap under each check."""
    r = pd.read_csv(DATA / "robustness.csv")
    short = {
        "Main result (model A, all controls)": "Main result (all controls)",
        "Superstar = All-NBA that season": "Superstar = All-NBA",
        "All-NBA, same player (fixed effects)": "All-NBA, same player",
        "Two groups: superstar vs everyone else": "Superstar vs everyone else",
        "Role players who were never All-Stars": "Never-All-Star role players",
        "Game days only": "Game days only",
        "Non-game days only": "Other days only",
        "Game days, same player (fixed effects)": "Game days, same player",
        "Non-game days, same player (fixed effects)": "Other days, same player",
        "NBA Finals only": "NBA Finals only",
        "Without LeBron James": "Without LeBron James",
        "Without the 10 most-interviewed players": "Without the 10 most-interviewed",
        "Question topics from LDA with K = 5": "5 question topics instead of 10",
        "Each unit weighted equally (linear model)": "Each unit weighted equally",
        "Season fixed effects (era)": "Season fixed effects (era)",
    }
    r = r.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(W, 7.4))
    ax.axvline(0, color="#999999", lw=1.2)
    for i, row in r.iterrows():                 # every check drawn the same way (all were planned or added openly)
        main = row.group == "Main"
        c = COL["superstar"]
        ax.plot([100 * row.diff_lo, 100 * row.diff_hi], [i, i], color=c, lw=3 if not main else 4, solid_capstyle="round")
        ax.plot(100 * row["diff"], i, "o", ms=11 if not main else 14, color=c, mec="white", mew=1.5)
        ax.text(100 * row.diff_hi + 0.4, i, f"{pp(row['diff'])} {ci(row.diff_lo, row.diff_hi)}", va="center",
                fontsize=13.5, color=INK, fontweight="bold" if main else "normal")
    ax.set_yticks(range(len(r)), [short[c] for c in r.check], fontsize=15)
    for lab in ax.get_yticklabels():
        if lab.get_text().startswith("Main"):
            lab.set_fontweight("bold")
    for i in range(1, len(r)):                  # a divider between groups of checks
        if r.group[i] != r.group[i - 1]:
            ax.axhline(i - 0.5, color=GRID, lw=1)
    ax.set_xlim(-10, 17.5)
    ax.set_ylim(-0.6, len(r) - 0.4)
    ax.set_xlabel("Superstar minus role player, adjusted we-share (percentage points)")
    clean(ax, None)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    note(fig, "Model A (all controls) re-run under each check; 95% CIs, SEs clustered by player. Never-All-Star role "
              "players and season fixed effects were added on 18 Nov.\nGame days only is the one interval that "
              "excludes zero; it is partly selection, because role players reach post-game podiums after their "
              "own big games.")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save(fig, "s07b_robustness.png")


def fig_we_check():
    """Slide 4: what "we" means (hand-coded sample)."""
    s = pd.read_csv(DATA / "we_sample.csv")
    tcol, ccol = "tier", "referent"
    fig, ax = plt.subplots(figsize=(W, 3.8))
    order = ["superstar", "starter", "role"]
    for i, t in enumerate(order):
        d = s[s[tcol] == t]
        k, n = int((d[ccol] == "team").sum()), len(d)
        p = k / n
        z = 1.96
        centre = (p + z * z / (2 * n)) / (1 + z * z / n)
        half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        ax.barh(i, 100 * p, color=COL[t], height=0.6)
        ax.plot([100 * (centre - half), 100 * (centre + half)], [i, i], color=INK, lw=2)
        ax.text(2, i, f"{k} of {n}", va="center", color="white", fontsize=17, fontweight="bold")
    ax.set_yticks(range(3), [NAME[t] for t in order], fontsize=18)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Uses of \"we\" that refer to the player's team (%)")
    clean(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    note(fig, "30 random uses per tier, one per player, read in context. Black lines: 95% Wilson intervals. "
              "Coder 1 (shown) saw the tier.\nA second coder blind to tier (a separate AI instance) agreed on 94% of uses "
              "(Cohen's kappa 0.76); team uses: superstar 26, starter 26, role player 25 of 30.")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save(fig, "s04_we_check.png")


def main():
    e, u_model = situation_effects()
    u = load_units()                     # 4,425 units with questions (the LDA / model sample)
    fig_data(u)
    fig_we_check()
    fig_main()
    fig_situation(e)
    fig_words()
    fig_classifiers()
    fig_topics(u)
    fig_robustness()


if __name__ == "__main__":
    main()
