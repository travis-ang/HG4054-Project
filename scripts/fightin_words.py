"""Step 10: Fightin' Words (Monroe, Colaresi & Quinn, 2008). Which words most separate superstars' answers
from role players' answers?

cd scripts && python fightin_words.py

Method: log-odds ratio with an informative Dirichlet prior (background = all player answers, every tier),
z-score = difference / its standard error. Names of players, coaches, teams and cities are removed (a word is a
name if it is written with a capital letter mid-sentence more than half the time in the answers).
Function words and pronouns are kept, because pronouns are the point.

Player-level checks for the top words (z-scores treat every word as independent, but words cluster by speaker):
number of players who use the word, share of the group's uses from its top player, and a Mann-Whitney test of
per-player rates (players with at least 500 words in that tier).

Writes data/fightin_words.csv (every word), data/fightin_words.txt, figures/fightin_words.png.
"""
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import lda_questions as L

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG = ROOT / "data", ROOT / "figures"
A, B = "superstar", "role"
I_WORDS = "i me my mine myself i'm i've i'll i'd".split()
WE_WORDS = "we us our ours ourselves we're we've we'll we'd".split()
KEEP = set(I_WORDS) | set(WE_WORDS) | {"you", "he", "she", "they", "it", "god"}   # never treated as names
TRANSCRIPT = set(L.TRANSCRIPT) | {"smiling", "laughing", "chuckles"}
MIN_COUNT, MIN_PLAYERS, MIN_WORDS_PLAYER = 20, 10, 500
PRIOR_SCALE = 0.1          # prior counts = 10% of each word's count in all player answers
TOP = 20


def tokens(text):
    t = re.sub(r"\([^)]{0,60}\)", " ", str(text))           # stenographer notes: (Laughter.), (Indiscernible)
    t = t.lower().replace("’", "'").replace("‘", "'")
    return re.findall(r"[a-z]+(?:'[a-z]+)?", t)


def name_words(texts):
    cand = L.name_tokens() - KEEP
    share = L.capitalised_share(texts, cand)
    return {w for w, s in share.items() if s > 0.5}


def fightin(ya, yb, prior):
    """Monroe et al. (2008) eq. 22: log-odds ratio with informative Dirichlet prior, and its z-score."""
    a0, na, nb = prior.sum(), ya.sum(), yb.sum()
    da = np.log((ya + prior) / (na + a0 - ya - prior))
    db = np.log((yb + prior) / (nb + a0 - yb - prior))
    delta = da - db
    var = 1 / (ya + prior) + 1 / (yb + prior)
    return delta, delta / np.sqrt(var)


def main():
    ans = pd.read_csv(DATA / "answers_analysis.csv")
    ans = ans[ans.tier.isin(["role", "starter", "superstar"])].reset_index(drop=True)
    names = name_words(ans.answer)
    toks = ans.answer.map(tokens)

    def clean(ws):
        out = []
        for w in ws:
            base = w[:-2] if w.endswith("'s") else w
            if base in names or w in TRANSCRIPT or base in TRANSCRIPT:
                continue
            out.append(w)
        return out
    toks = toks.map(clean)

    # counts per tier and per (tier, player)
    tier_c = {t: Counter() for t in ["role", "starter", "superstar"]}
    player_c = {}
    for t, p, ws in zip(ans.tier, ans.person_key, toks):
        tier_c[t].update(ws)
        player_c.setdefault((t, p), Counter()).update(ws)
    background = tier_c["role"] + tier_c["starter"] + tier_c["superstar"]

    users = Counter()                                              # distinct players using each word (A or B)
    for (t, p), c in player_c.items():
        if t in (A, B):
            users.update(c.keys())
    vocab = sorted(w for w in background if tier_c[A][w] + tier_c[B][w] >= MIN_COUNT and users[w] >= MIN_PLAYERS)
    # pronoun families as extra pseudo-words
    fam = {"[I words]": I_WORDS, "[we words]": WE_WORDS}
    for f, ws in fam.items():
        for c in list(tier_c.values()) + [background]:
            c[f] = sum(c[w] for w in ws)
    ya = np.array([tier_c[A][w] for w in vocab], float)
    yb = np.array([tier_c[B][w] for w in vocab], float)
    bg = np.array([background[w] for w in vocab], float)

    out = pd.DataFrame({"word": vocab, "n_superstar": ya, "n_role": yb, "n_all": bg,
                        "rate_superstar": 1000 * ya / ya.sum(), "rate_role": 1000 * yb / yb.sum(),
                        "players": [users[w] for w in vocab]})
    for s in (0.01, PRIOR_SCALE, 1.0):
        d, z = fightin(ya, yb, s * bg)
        out[f"z_{s:g}"] = z
        if s == PRIOR_SCALE:
            out["delta"], out["z"] = d, z
    out = out.sort_values("z", ascending=False).reset_index(drop=True)
    out["rank_superstar"] = np.arange(1, len(out) + 1)
    out["rank_role"] = out.z.rank(ascending=True).astype(int)

    # pronoun families (computed on the same totals as the vocabulary)
    fam_rows = []
    for f, ws in fam.items():
        fa, fb, fbg = tier_c[A][f], tier_c[B][f], background[f]
        prior_all = np.append(PRIOR_SCALE * bg, PRIOR_SCALE * fbg)
        d, z = fightin(np.append(ya, fa), np.append(yb, fb), prior_all)
        fam_rows.append((f, fa, fb, 1000 * fa / ya.sum(), 1000 * fb / yb.sum(), z[-1]))

    # player-level checks for the top words on each side
    rates = {}
    for (t, p), c in player_c.items():
        n = sum(c.values())
        if t in (A, B) and n >= MIN_WORDS_PLAYER:
            rates[(t, p)] = (c, n)

    def player_check(w):
        ra = [1000 * c[w] / n for (t, p), (c, n) in rates.items() if t == A]
        rb = [1000 * c[w] / n for (t, p), (c, n) in rates.items() if t == B]
        side = A if out.loc[out.word == w, "z"].iloc[0] > 0 else B
        contrib = Counter({p: c[w] for (t, p), c in player_c.items() if t == side})
        top_p, top_n = contrib.most_common(1)[0]
        total = tier_c[side][w]
        return dict(word=w, med_superstar=np.median(ra), med_role=np.median(rb),
                    mw_p=mannwhitneyu(ra, rb).pvalue, top_player=top_p, top_share=top_n / total,
                    players_side=sum(1 for v in contrib.values() if v > 0))

    top_a, top_b = out.head(TOP), out.tail(TOP).iloc[::-1]
    checks = pd.DataFrame([player_check(w) for w in list(top_a.word) + list(top_b.word)])
    n_pa = sum(1 for (t, _) in rates if t == A)
    n_pb = sum(1 for (t, _) in rates if t == B)
    out = out.merge(checks, on="word", how="left")
    out.to_csv(DATA / "fightin_words.csv", index=False)

    # sensitivity of the top lists to the prior
    def overlap(col):
        o = out.sort_values(col, ascending=False)
        return (len(set(o.word.head(TOP)) & set(top_a.word)), len(set(o.word.tail(TOP)) & set(top_b.word)))

    lines = [f"Step 10 Fightin' Words: {A} vs {B} answers (Monroe, Colaresi & Quinn 2008, informative Dirichlet prior).",
             f"Tokens after cleaning: superstar {int(ya.sum()):,} / role {int(yb.sum()):,} (in-vocabulary); "
             f"vocabulary {len(vocab):,} words (>= {MIN_COUNT} uses in the two groups, used by >= {MIN_PLAYERS} players).",
             f"Name words removed: {len(names)} (e.g. {', '.join(sorted(names)[:25])}).",
             f"Prior: {PRIOR_SCALE:g} x each word's count in all player answers (role + starter + superstar).",
             f"Words with |z| > 1.96: {(out.z.abs() > 1.96).sum()} of {len(out)} "
             f"({(out.z > 1.96).sum()} superstar side, {(out.z < -1.96).sum()} role side).",
             f"Player-level test: players with >= {MIN_WORDS_PLAYER} words in that tier: superstar {n_pa}, role {n_pb}.",
             "",
             "Pronoun families (z > 0 = more superstar):"]
    for f, fa, fb, ra, rb, z in fam_rows:
        lines.append(f"  {f:<11} superstar {ra:.1f} / role {rb:.1f} per 1,000 words, z = {z:+.2f}")
    lines.append("Single pronouns:")
    for w in I_WORDS + WE_WORDS + ["you"]:
        r = out[out.word == w]
        if len(r):
            r = r.iloc[0]
            lines.append(f"  {w:<10} z = {r.z:+6.2f}  rank {int(r.rank_superstar)} of {len(out)} from the superstar end  "
                         f"({r.rate_superstar:.2f} vs {r.rate_role:.2f} per 1,000)")
    for side, tab in [("SUPERSTAR", top_a), ("ROLE PLAYER", top_b)]:
        lines += ["", f"Top {TOP} {side} words: z | per 1,000 words superstar vs role | players using | "
                      f"player medians superstar vs role, Mann-Whitney p | top player's share of uses"]
        for w in tab.word:
            r = out[out.word == w].iloc[0]
            lines.append(f"  {w:<14} {r.z:+6.2f} | {r.rate_superstar:6.2f} vs {r.rate_role:6.2f} | {int(r.players):>3} | "
                         f"{r.med_superstar:5.2f} vs {r.med_role:5.2f}, p={r.mw_p:.3f} | {r.top_player} {r.top_share:.0%}")
    lines += ["", f"Top-{TOP} overlap with other priors (superstar list, role list):"]
    for s in (0.01, 1.0):
        lines.append(f"  prior {s:g} x background: {overlap(f'z_{s:g}')}")
    lines += split_by_session(ans, toks)
    txt = "\n".join(lines) + "\n"
    (DATA / "fightin_words.txt").write_text(txt, encoding="utf-8")
    print(txt)
    figure(out, top_a, top_b, fam_rows)


def split_by_session(ans, toks, n=15):
    """Superstars give more post-game interviews, so game words may reflect session, not status.
    Re-run within game days and within other days (same prior rule, same vocabulary rules)."""
    lines = ["", "Within session (superstars do more post-game interviews; this separates session from status):"]
    for gd, label in [(1, "GAME DAYS"), (0, "NON-GAME DAYS")]:
        c = {t: Counter() for t in ["role", "starter", "superstar"]}
        users, seen = Counter(), set()
        for t, p, g, ws in zip(ans.tier, ans.person_key, ans.game_day, toks):
            if g != gd:
                continue
            c[t].update(ws)
            if t in (A, B):
                for w in set(ws):
                    if (p, w) not in seen:
                        seen.add((p, w))
                        users[w] += 1
        bgc = c["role"] + c["starter"] + c["superstar"]
        vocab = sorted(w for w in bgc if c[A][w] + c[B][w] >= MIN_COUNT and users[w] >= MIN_PLAYERS)
        for f, ws in {"[I words]": I_WORDS, "[we words]": WE_WORDS}.items():
            for cc in list(c.values()) + [bgc]:
                cc[f] = sum(cc[w] for w in ws)
        vocab_f = vocab + ["[I words]", "[we words]"]
        ya = np.array([c[A][w] for w in vocab_f], float)
        yb = np.array([c[B][w] for w in vocab_f], float)
        _, z = fightin(ya, yb, PRIOR_SCALE * np.array([bgc[w] for w in vocab_f], float))
        zf = dict(zip(vocab_f, z))
        o = pd.Series(z[:-2], index=vocab).sort_values(ascending=False)
        lines.append(f"  {label}: tokens superstar {int(ya[:-2].sum()):,} / role {int(yb[:-2].sum()):,}; vocabulary {len(vocab):,}; "
                     f"|z| > 1.96: {(o.abs() > 1.96).sum()}. I words z = {zf['[I words]']:+.2f}, we words z = {zf['[we words]']:+.2f}, "
                     f"i z = {zf.get('i', np.nan):+.2f}, we z = {zf.get('we', np.nan):+.2f}")
        lines.append("    superstar: " + ", ".join(f"{w} {v:+.1f}" for w, v in o.head(n).items()))
        lines.append("    role:      " + ", ".join(f"{w} {v:+.1f}" for w, v in o.tail(n).iloc[::-1].items()))
    return lines


def figure(out, top_a, top_b, fam_rows, n=15):
    a = top_a.head(n).iloc[::-1]
    b = top_b.head(n).iloc[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(10, 6.2), sharex=False)
    for ax, tab, col, title in [(axes[0], b, "#eb6834", "Role players use more"),
                                (axes[1], a, "#2a78d6", "Superstars use more")]:
        y = np.arange(len(tab))
        ax.barh(y, tab.z.abs(), color=col, height=0.62)
        ax.set_yticks(y, tab.word)
        ax.set_title(title, loc="left", fontsize=11)
        ax.set_xlabel("|z-score|")
        ax.axvline(1.96, color="#999999", lw=1, ls="--")
        ax.grid(axis="x", color="#eeeeee", lw=0.8)
        ax.set_axisbelow(True)
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
    xmax = max(a.z.abs().max(), b.z.abs().max()) * 1.05
    for ax in axes:
        ax.set_xlim(0, xmax)                      # same scale on both sides
    zi = dict((f, z) for f, *_, z in fam_rows)
    fig.suptitle("Words that most separate superstars' and role players' answers", x=0.01, ha="left", y=0.985, fontsize=13)
    fig.text(0.01, 0.01, f"Fightin' Words (log-odds, informative Dirichlet prior), names removed. Dashed line: |z| = 1.96. "
             f"Pronoun families: \"I\" words z = {zi['[I words]']:+.1f}, \"we\" words z = {zi['[we words]']:+.1f}.",
             fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "fightin_words.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
