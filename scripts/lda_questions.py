"""Step 7: LDA topics of the reporters' questions (used as controls in the main models).

python scripts/lda_questions.py sweep          # compare K = 5, 8, 10, 12, 15, 20 -> data/lda_sweep.txt
python scripts/lda_questions.py fit K          # final model with K topics -> data/unit_topics.csv,
                                               #   data/lda_topics.txt, figures/topics_by_tier.png

Documents: one per unit (all the reporters' questions to one player in one press conference).
Counts, not TF-IDF: LDA models raw word counts.
"""
import re
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
KS = [5, 8, 10, 12, 15, 20]
SEEDS = [0, 1, 2]
TOP_N = 10          # words per topic used for coherence and stability of the word lists

# --- vocabulary settings ------------------------------------------------------
MIN_DF = 10         # word must appear in at least 10 documents (drops typos and one-off words)
MAX_DF = 0.5        # and in at most half of them (too common to separate topics)
MAX_FEATURES = 5000
NGRAMS = (1, 2)     # single words and two-word phrases ("game seven", "free throws")

# Spoken filler that the standard stopword list misses
FILLER = """know just like think talk talking obviously guys going gonna really lot thing things
little bit sort kind say saying said mean got get getting did does doing question maybe want
way come came yeah okay ok sure actually able look looks looked tell told seen let make
make makes made right good great definitely course pretty especially certainly""".split()

# Pass 2 (after reading the first sweep): words that sat near the top of almost every topic
# without saying what the question is about, and stenographer notes (these vary by year and
# stenographer, so they would bring era into the controls).
GENERIC = """feel feeling felt series play playing played plays games time times different point
big coming talked having couple went better away people""".split()
TRANSCRIPT = """inaudible indiscernible microphone unintelligible crosstalk laughter applause""".split()

# Teams, short forms and cities (removed if they are written as names in the questions)
PLACES = """hawks celtics nets hornets bobcats bulls cavaliers cavs mavericks mavs nuggets pistons
warriors dubs rockets pacers clippers lakers grizzlies heat bucks timberwolves wolves pelicans
hornets knicks thunder magic sixers raptors suns blazers trail kings spurs jazz wizards
supersonics sonics atlanta boston brooklyn jersey charlotte chicago cleveland dallas denver
detroit golden state oakland houston indiana indianapolis angeles los clippers memphis miami
milwaukee minnesota orleans york oklahoma orlando philadelphia philly phoenix portland
sacramento antonio toronto utah washington seattle san bay""".split()
NICKNAMES = """steph kd bron lebron dray klay giannis melo shaq kobe dirk timmy manu ad cp jt jb
spo pop bosh wade dwyane""".split()


def name_tokens():
    """Candidate name words: every player, coach and All-Star name, plus teams and cities."""
    names = set()
    for f, col in [("nba_season_starts.csv", "player"), ("nba_playoff_gamelogs.csv", "player"),
                   ("coaches.csv", "coach"), ("allstars.csv", "player")]:
        for n in pd.read_csv(D / f)[col].dropna().unique():
            names.update(re.findall(r"[a-z]+", n.lower()))
    return names | set(PLACES) | set(NICKNAMES)


def capitalised_share(texts, words):
    """For each word, share of its mid-sentence uses that are capitalised (a proper noun)."""
    cap, low = {}, {}
    for t in texts:
        for m in re.finditer(r"(?<![.?!]\s)(?<!^)\b([A-Za-z]+)\b", t):
            w = m.group(1)
            k = w.lower()
            if k in words:
                if w[0].isupper():
                    cap[k] = cap.get(k, 0) + 1
                else:
                    low[k] = low.get(k, 0) + 1
    return {k: cap.get(k, 0) / (cap.get(k, 0) + low.get(k, 0)) for k in set(cap) | set(low)}


PLURAL = {}   # plural -> singular, filled by build_matrix from the corpus itself


def clean(t):
    t = t.lower().replace("’", "'")
    t = re.sub(r"'s\b", "", t)                 # possessive
    t = re.sub(r"\b[a-z]+'[a-z]+\b", " ", t)   # contractions (don't, you're) are function words
    if PLURAL:
        t = re.sub(r"\b[a-z]+s\b", lambda m: PLURAL.get(m.group(0), m.group(0)), t)
    return t


def plural_map(texts):
    """Fold a plural into its singular when both forms occur (shots -> shot, throws -> throw)."""
    words = set()
    for t in texts:
        words.update(re.findall(r"\b[a-z]{3,}\b", clean(t)))
    return {w: w[:-1] for w in words if w.endswith("s") and not w.endswith("ss") and w[:-1] in words}


def load():
    u = pd.read_csv(D / "units.csv")
    u = u[(u.tier != "unknown") & u.questions.notna() & (u.q_words > 0)].reset_index(drop=True)
    return u


def build_matrix(u):
    cand = name_tokens()
    share = capitalised_share(u.questions, cand)
    names = {w for w, s in share.items() if s > 0.5}   # written as a name more often than not
    PLURAL.clear()
    PLURAL.update(plural_map(u.questions))
    stop = set(ENGLISH_STOP_WORDS) | set(FILLER) | set(GENERIC) | set(TRANSCRIPT) | names
    stop = sorted(stop | {PLURAL.get(w, w) for w in stop})   # stop the singular form too
    vec = CountVectorizer(preprocessor=clean, token_pattern=r"(?u)\b[a-z]{3,}\b", stop_words=stop,
                          min_df=MIN_DF, max_df=MAX_DF, max_features=MAX_FEATURES, ngram_range=NGRAMS)
    X = vec.fit_transform(u.questions)
    # words dropped by max_df (too common): reported, not used
    full = CountVectorizer(preprocessor=clean, token_pattern=r"(?u)\b[a-z]{3,}\b", stop_words=stop,
                           min_df=MIN_DF).fit(u.questions)
    dfreq = (full.transform(u.questions) > 0).mean(axis=0).A1
    too_common = [w for w, f in sorted(zip(full.get_feature_names_out(), dfreq), key=lambda x: -x[1])
                  if f > MAX_DF]
    return X, vec, sorted(names), too_common


def fit(X, k, seed, alpha=None):
    return LatentDirichletAllocation(n_components=k, doc_topic_prior=alpha, topic_word_prior=None,
                                     learning_method="batch", max_iter=50, random_state=seed, n_jobs=-1).fit(X)


def top_words(lda, vocab, n=TOP_N):
    return [[vocab[i] for i in comp.argsort()[::-1][:n]] for comp in lda.components_]


def npmi_coherence(lda, Xbin, n=TOP_N):
    """Mean NPMI of top-word pairs, from document co-occurrence in the corpus (higher = the top
    words of a topic tend to appear in the same documents)."""
    N = Xbin.shape[0]
    scores = []
    for comp in lda.components_:
        idx = comp.argsort()[::-1][:n]
        sub = Xbin[:, idx].toarray()
        p = sub.mean(axis=0)
        s = []
        for a, b in combinations(range(n), 2):
            pab = (sub[:, a] & sub[:, b]).sum() / N
            if pab == 0:
                s.append(-1.0)
            else:
                s.append(np.log(pab / (p[a] * p[b])) / -np.log(pab))
        scores.append(np.mean(s))
    return float(np.mean(scores)), scores


def diversity(lda, vocab, n=25):
    """Share of unique words among all topics' top-25 lists (low = topics repeat each other)."""
    tw = top_words(lda, vocab, n)
    return len({w for t in tw for w in t}) / (n * len(tw))


def stability(models):
    """Match topics between seeds (Hungarian, cosine of topic-word distributions); mean similarity."""
    def norm(m):
        c = m.components_ / m.components_.sum(1, keepdims=True)
        return c / np.linalg.norm(c, axis=1, keepdims=True)
    sims = []
    for a, b in combinations(models, 2):
        S = norm(a) @ norm(b).T
        r, c = linear_sum_assignment(-S)
        sims.append(S[r, c].mean())
    return float(np.mean(sims))


def sweep():
    u = load()
    X, vec, names, too_common = build_matrix(u)
    vocab = vec.get_feature_names_out()
    Xbin = (X > 0).astype(np.int8).tocsc()
    out = [f"Documents (units with questions): {X.shape[0]:,}   vocabulary: {X.shape[1]:,} terms   "
           f"median words kept per document: {int(np.median(X.sum(1).A1))}",
           f"Name words removed ({len(names)}), e.g.: {', '.join(names[:40])}",
           f"Removed as too common (in > {MAX_DF:.0%} of documents): {', '.join(too_common)}", ""]
    rows = []
    for k in KS:
        models = [fit(X, k, s) for s in SEEDS]
        coh, per = npmi_coherence(models[0], Xbin)
        rows.append((k, coh, diversity(models[0], vocab), stability(models)))
        out.append(f"K = {k}: NPMI coherence {coh:.3f}  diversity {rows[-1][2]:.2f}  "
                   f"seed stability {rows[-1][3]:.2f}")
        for i, (t, c) in enumerate(zip(top_words(models[0], vocab, 12), per)):
            out.append(f"   {i + 1:>2} ({c:+.2f}) {', '.join(t)}")
        out.append("")
        print(out[-k - 2], flush=True)
    tab = pd.DataFrame(rows, columns=["K", "npmi", "diversity", "stability"])
    out.insert(3, "Summary\n" + tab.round(3).to_string(index=False) + "\n")
    (D / "lda_sweep.txt").write_text("\n".join(out), encoding="utf-8")
    tab.to_csv(D / "lda_sweep.csv", index=False)
    print(tab.round(3).to_string(index=False))


def final(k):
    u = load()
    X, vec, names, _ = build_matrix(u)
    vocab = vec.get_feature_names_out()
    Xbin = (X > 0).astype(np.int8).tocsc()
    models = [fit(X, k, s) for s in SEEDS]
    lda = models[0]
    theta = lda.transform(X)
    cols = [f"topic_{i + 1}" for i in range(k)]
    labels = LABELS.get(k, {})
    out = u[["interview_id", "person_key", "tier"]].copy()
    out[cols] = theta
    out.drop(columns="tier").to_csv(D / "unit_topics.csv", index=False)

    # per-topic stability: best cosine match of each seed-0 topic in the seed-1 and seed-2 models
    def norm(m):
        c = m.components_ / m.components_.sum(1, keepdims=True)
        return c / np.linalg.norm(c, axis=1, keepdims=True)
    stab = np.mean([(norm(lda) @ norm(m).T)[np.arange(k), linear_sum_assignment(-(norm(lda) @ norm(m).T))[1]]
                    for m in models[1:]], axis=0)

    lines = [f"Final model: K = {k}, seed 0, alpha = eta = 1/K, batch, 50 iterations", "",
             "topic (NPMI coherence, stability across seeds): label | top 15 words"]
    coh, per = npmi_coherence(lda, Xbin)
    rows = []
    for i, (t, c) in enumerate(zip(top_words(lda, vocab, 15), per)):
        lab = labels.get(i + 1, "")
        rows.append((f"topic_{i + 1}", lab, round(c, 3), round(float(stab[i]), 2), ", ".join(t)))
        lines.append(f"topic_{i + 1} ({c:+.2f}, {stab[i]:.2f}): {lab} | {', '.join(t)}")
    pd.DataFrame(rows, columns=["topic", "label", "npmi", "stability", "top_words"]).to_csv(
        D / "topic_labels.csv", index=False)
    lines.append("")
    share = out.groupby("tier")[cols].mean().T
    share.index = [f"{c} {labels.get(i + 1, '')}" for i, c in enumerate(cols)]
    lines.append("Mean topic share by tier (descriptive; no controls):")
    lines.append(share[["role", "starter", "superstar"]].round(3).to_string())
    lines.append("")
    plot_tiers(out, cols, labels)
    lines.append("Alpha sensitivity (NPMI coherence, diversity). Same 10 themes at all three values:")
    for a in [1 / k, 0.5, 1.0]:
        m = fit(X, k, 0, alpha=a)
        lines.append(f"  alpha = {a:.3f}: {npmi_coherence(m, Xbin)[0]:.3f}, {diversity(m, vocab):.2f}")
    (D / "lda_topics.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


TIERS = [("role", "Role player", "#eb6834"), ("starter", "Starter", "#1baf7a"),
         ("superstar", "Superstar", "#2a78d6")]


def plot_tiers(out, cols, labels):
    """Dot plot: mean share of each question topic, by tier (topics sorted by superstar - role)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    m = out.groupby("tier")[cols].mean().T
    m["gap"] = m["superstar"] - m["role"]
    m = m.sort_values("gap")
    names = [labels.get(int(c.split("_")[1]), c) for c in m.index]
    fig, ax = plt.subplots(figsize=(8, 5.2))
    y = np.arange(len(m))
    for yy, (_, r) in zip(y, m.iterrows()):
        ax.plot([r[["role", "starter", "superstar"]].min(), r[["role", "starter", "superstar"]].max()],
                [yy, yy], color="#d0d0cc", lw=2, zorder=1)
    for key, name, col in TIERS:
        ax.scatter(m[key], y, s=64, color=col, label=name, zorder=3, edgecolor="white", linewidth=1.5)
    ax.set_yticks(y, names)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlabel("Average share of the reporters' questions")
    fig.suptitle("What reporters ask about, by player tier", x=0.01, y=0.985, ha="left", fontsize=13)
    ax.grid(axis="x", color="#ececea", lw=0.8)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.legend(*ax.get_legend_handles_labels(), frameon=False, ncol=3, loc="upper right",
               bbox_to_anchor=(0.99, 0.995), handletextpad=0.2, columnspacing=1.2)
    fig.text(0.01, 0.01, "LDA, 10 topics, 4,425 player press conferences. Topics sorted by superstar minus "
             "role player. Descriptive, no controls.", fontsize=8, color="#666")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(ROOT / "figures" / "topics_by_tier.png", dpi=200)


# Names given after reading each topic's top 15 words (K = 10, seed 0)
LABELS = {10: {
    1: "Season and playoff run",
    2: "First half: fouls and turnovers",
    3: "Fourth quarter and closing",
    4: "Championship and legacy",
    5: "Tactics and adjustments",
    6: "Shooting and free throws",
    7: "Pressure and mindset",
    8: "The Finals stage",
    9: "Individual performance",
    10: "Home court and the series",
}}


if __name__ == "__main__":
    if sys.argv[1] == "sweep":
        sweep()
    else:
        final(int(sys.argv[2]))
