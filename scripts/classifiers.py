"""Step 11: classifiers. Can a model tell a superstar's press conference from a role player's, and is the
difference just pronouns?

cd scripts && python classifiers.py            (first run embeds every answer with MiniLM, about 5-10 min on CPU;
                                                the embeddings are cached in data/answer_embeddings_minilm.npy)

Unit: one player in one press conference (units.csv), superstars (1) against role players (0); starters left out,
as in Step 10. All of a player's units are kept in the same fold (grouped by player), so a model can never
recognise a player it has seen in training; a player who changes tier stays in one fold with all his units.

Models (all logistic regression, class weights balanced):
  B1  session and round only (game day, round dummies)         -> how much is the situation
  B2  length only (log words, log number of answers)           -> how much is talking more
  E1  pronoun rates only ("I" and "we" per 1,000 words, we-share)
  E2  bag of words: tf-idf of single words, names removed (Step 10 rule)
  E2b E2 without the "I" and "we" words                        -> is the difference just pronouns?
  E3  sentence embeddings: all-MiniLM-L6-v2, mean of each answer's embedding (long answers split into
      200-word chunks), averaged over the unit's answers
Regularisation C for E2, E2b and E3 is chosen inside each training fold (3-fold, grouped by player).

Evaluation: 5-fold cross-validation grouped by player and stratified by tier, repeated with 5 seeds.
Out-of-fold ROC AUC (0.5 = chance) and balanced accuracy. 95% CIs and paired differences between models from a
bootstrap over players (2,000 resamples) on the seed-0 predictions. AUC is also computed within game days, within
non-game days and within length fifths (average of the within-group AUCs), to see what is left beyond session
and length.

Writes data/classifier_results.txt, data/classifier_results.csv, data/classifier_words.csv,
figures/classifiers.png.
"""
import re
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, GroupKFold, StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import fightin_words as F

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG = ROOT / "data", ROOT / "figures"
EMB_FILE = DATA / "answer_embeddings_minilm.npy"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SEEDS, FOLDS, BOOT = range(5), 5, 2000
GRID = {"logisticregression__C": [0.03, 0.1, 0.3, 1, 3, 10]}
PRONOUNS = set(F.I_WORDS) | set(F.WE_WORDS)
MODELS = {"B1": "Session and round only", "B2": "Length only", "E1": "Pronoun rates only",
          "E2": "Bag of words", "E2b": "Bag of words without I/we", "E3": "Sentence embeddings (MiniLM)"}


def identity(x):
    return x


def load():
    ans = pd.read_csv(DATA / "answers_analysis.csv")
    ans = ans[ans.tier.isin(["role", "starter", "superstar"])].reset_index(drop=True)
    names = F.name_words(ans.answer)

    def clean(ws):
        out = []
        for w in ws:
            base = w[:-2] if w.endswith("'s") else w
            if base in names or w in F.TRANSCRIPT or base in F.TRANSCRIPT:
                continue
            out.append(w)
        return out
    ans["toks"] = ans.answer.map(F.tokens).map(clean)
    ans["emb_row"] = np.arange(len(ans))
    two = ans[ans.tier.isin(["role", "superstar"])]
    units = (two.groupby(["interview_id", "person_key"], sort=False)
             .agg(tier=("tier", "first"), game_day=("game_day", "first"), round=("round", "first"),
                  words=("words", "sum"), n_answers=("answer", "size"), i_count=("i_count", "sum"),
                  we_count=("we_count", "sum"), toks=("toks", lambda s: [w for ws in s for w in ws]),
                  emb_rows=("emb_row", list))
             .reset_index())
    units["y"] = (units.tier == "superstar").astype(int)
    return ans, units, names


def embed(ans):
    """MiniLM sentence embedding of every answer (all tiers), cached. Long answers: 200-word chunks, averaged."""
    if EMB_FILE.exists():
        e = np.load(EMB_FILE)
        if len(e) == len(ans):
            return e
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.set_num_threads(12)
    tok, model = AutoTokenizer.from_pretrained(EMB_MODEL), AutoModel.from_pretrained(EMB_MODEL).eval()
    chunks, owner = [], []
    for i, text in enumerate(ans.answer.astype(str)):
        text = re.sub(r"\([^)]{0,60}\)", " ", text)
        ws = text.split() or [""]
        for k in range(0, len(ws), 200):
            chunks.append(" ".join(ws[k:k + 200]))
            owner.append(i)
    order = np.argsort([len(c) for c in chunks])                  # batch similar lengths together
    out = np.zeros((len(chunks), 384), np.float32)
    t0 = time.time()
    with torch.inference_mode():
        for b in range(0, len(order), 128):
            idx = order[b:b + 128]
            enc = tok([chunks[i] for i in idx], padding=True, truncation=True, max_length=256, return_tensors="pt")
            h = model(**enc).last_hidden_state
            m = enc["attention_mask"].unsqueeze(-1).float()
            v = (h * m).sum(1) / m.sum(1)
            out[idx] = torch.nn.functional.normalize(v, dim=1).numpy()
            if b % 5120 == 0:
                print(f"  embedded {b}/{len(order)} chunks, {time.time() - t0:.0f} s", flush=True)
    owner = np.array(owner)
    e = np.zeros((len(ans), 384), np.float32)
    np.add.at(e, owner, out)
    e /= np.bincount(owner, minlength=len(ans))[:, None]
    np.save(EMB_FILE, e)
    print(f"  {len(chunks)} chunks for {len(ans)} answers ({len(chunks) - len(ans)} extra from long answers)")
    return e


def features(u, emb):
    w = u.words.clip(lower=1)
    pron = (u.i_count + u.we_count)
    X = {
        "B1": pd.get_dummies(u["round"], drop_first=True).assign(game_day=u.game_day).astype(float).values,
        "B2": np.c_[np.log(w), np.log(u.n_answers)],
        "E1": np.c_[1000 * u.i_count / w, 1000 * u.we_count / w,
                    np.where(pron > 0, u.we_count / pron.clip(lower=1), 0.5)],
        "E2": u.toks.tolist(),
        "E2b": [[t for t in ws if t not in PRONOUNS] for ws in u.toks],
        "E3": np.vstack([emb[r].mean(0) for r in u.emb_rows]),
    }
    return X


def make_model(kind):
    lr = LogisticRegression(class_weight="balanced", max_iter=5000)
    if kind in ("E2", "E2b"):
        pipe = make_pipeline(TfidfVectorizer(analyzer=identity, min_df=5, sublinear_tf=True), lr)
    else:
        pipe = make_pipeline(StandardScaler(), lr)
    if kind in ("E2", "E2b", "E3"):
        return GridSearchCV(pipe, GRID, cv=GroupKFold(3), scoring="roc_auc", n_jobs=-1)
    return pipe


def subset(X, idx):
    return [X[i] for i in idx] if isinstance(X, list) else X[idx]


def oof(kind, X, y, g, seed):
    p, chosen = np.zeros(len(y)), []
    cv = StratifiedGroupKFold(FOLDS, shuffle=True, random_state=seed)
    for tr, te in cv.split(np.zeros(len(y)), y, g):
        m = make_model(kind)
        if isinstance(m, GridSearchCV):
            m.fit(subset(X, tr), y[tr], groups=g[tr])
            chosen.append(m.best_params_["logisticregression__C"])
        else:
            m.fit(subset(X, tr), y[tr])
        p[te] = m.predict_proba(subset(X, te))[:, 1]
    return p, chosen


def within_auc(y, p, strata):
    """Average AUC within strata (weighted by stratum size), skipping strata with one class."""
    aucs, ns = [], []
    for s in np.unique(strata):
        k = strata == s
        if len(np.unique(y[k])) == 2:
            aucs.append(roc_auc_score(y[k], p[k]))
            ns.append(k.sum())
    return np.average(aucs, weights=ns)


def boot(y, preds, g, strata=None):
    """Bootstrap over players: CI of each model's AUC and of paired differences."""
    rng = np.random.default_rng(0)
    players = np.unique(g)
    rows = {p: np.flatnonzero(g == p) for p in players}
    res = {k: [] for k in preds}
    for _ in range(BOOT):
        idx = np.concatenate([rows[p] for p in rng.choice(players, len(players))])
        if len(np.unique(y[idx])) < 2:
            continue
        for k, p in preds.items():
            res[k].append(roc_auc_score(y[idx], p[idx]) if strata is None else within_auc(y[idx], p[idx], strata[idx]))
    return {k: np.array(v) for k, v in res.items()}


def main():
    t0 = time.time()
    ans, u, names = load()
    print(f"units: superstar {u.y.sum()}, role {(1 - u.y).sum()}, players {u.person_key.nunique()}")
    emb = embed(ans)
    X = features(u, emb)
    y, g = u.y.values, u.person_key.values
    gd = u.game_day.values
    lenq = pd.qcut(u.words, 5, labels=False).values

    preds, auc_seeds, bacc_seeds, Cs = {}, {k: [] for k in MODELS}, {k: [] for k in MODELS}, {}
    for k in MODELS:
        for s in SEEDS:
            p, chosen = oof(k, X[k], y, g, s)
            auc_seeds[k].append(roc_auc_score(y, p))
            bacc_seeds[k].append(balanced_accuracy_score(y, p > 0.5))
            if s == 0:
                preds[k], Cs[k] = p, chosen
        print(f"  {k}: AUC {np.mean(auc_seeds[k]):.3f} ({time.time() - t0:.0f} s)", flush=True)

    b_all = boot(y, preds, g)
    b_len = boot(y, preds, g, lenq)
    rows = []
    for k, name in MODELS.items():
        p = preds[k]
        rows.append(dict(
            model=k, name=name, auc=np.mean(auc_seeds[k]), auc_min=min(auc_seeds[k]), auc_max=max(auc_seeds[k]),
            auc_seed0=roc_auc_score(y, p), lo=np.percentile(b_all[k], 2.5), hi=np.percentile(b_all[k], 97.5),
            bal_acc=np.mean(bacc_seeds[k]),
            auc_gameday=roc_auc_score(y[gd == 1], p[gd == 1]), auc_other=roc_auc_score(y[gd == 0], p[gd == 0]),
            auc_within_session=within_auc(y, p, gd), auc_within_length=within_auc(y, p, lenq),
            len_lo=np.percentile(b_len[k], 2.5), len_hi=np.percentile(b_len[k], 97.5),
            C_chosen=",".join(f"{c:g}" for c in Cs[k]) if Cs[k] else ""))
    r = pd.DataFrame(rows)
    r.to_csv(DATA / "classifier_results.csv", index=False)

    def diff(a, b, bb=b_all):
        d = bb[a] - bb[b]
        return f"{d.mean():+.3f} [{np.percentile(d, 2.5):+.3f}, {np.percentile(d, 97.5):+.3f}]"

    # E2 weights fitted on all units: a second word list
    gm = make_model("E2").fit(X["E2"], y, groups=g)
    best = gm.best_estimator_
    vec, clf = best.named_steps["tfidfvectorizer"], best.named_steps["logisticregression"]
    coef = pd.DataFrame({"word": vec.get_feature_names_out(), "weight": clf.coef_[0]}).sort_values("weight")
    coef.to_csv(DATA / "classifier_words.csv", index=False)
    fw = pd.read_csv(DATA / "fightin_words.csv")
    fw_sup, fw_role = set(fw.head(20).word), set(fw.tail(20).word)
    top_sup = coef.tail(20).iloc[::-1]
    top_role = coef.head(20)

    L = []
    L.append("Step 11: classifiers, superstar vs role player press conferences (units), split grouped by player")
    L.append(f"Units: superstar {u.y.sum()}, role {(1 - u.y).sum()}; players {u.person_key.nunique()} "
             f"(tier changers kept in one fold). Game days: {gd.sum()} units, other days {(1 - gd).sum()}.")
    L.append(f"Median words per unit: superstar {u.words[y == 1].median():.0f}, role {u.words[y == 0].median():.0f}.")
    L.append(f"5-fold CV grouped by player, stratified, 5 seeds. AUC = mean over seeds (range); 95% CI from "
             f"{BOOT} player bootstrap resamples of seed 0.\n")
    L.append(f"{'model':<4} {'name':<30} {'AUC':>6} {'95% CI':>16} {'seeds':>13} {'bal.acc':>8} "
             f"{'game d.':>8} {'other':>6} {'w/in len':>9} {'95% CI':>16}")
    for _, x in r.iterrows():
        L.append(f"{x.model:<4} {x['name']:<30} {x.auc:6.3f} [{x.lo:.3f}, {x.hi:.3f}] "
                 f"[{x.auc_min:.3f}-{x.auc_max:.3f}] {x.bal_acc:8.3f} {x.auc_gameday:8.3f} {x.auc_other:6.3f} "
                 f"{x.auc_within_length:9.3f} [{x.len_lo:.3f}, {x.len_hi:.3f}]")
    L.append("\nC chosen in each outer fold (seed 0): " +
             "; ".join(f"{k} {c}" for k, c in zip(r.model, r.C_chosen) if c))
    L.append("\nPaired AUC differences (player bootstrap, seed 0), all units:")
    for a, b in [("E2", "E2b"), ("E2", "E1"), ("E3", "E2"), ("E1", "B2"), ("E2", "B1"), ("E2", "B2")]:
        L.append(f"  {a} - {b}: {diff(a, b)}")
    L.append("Within length fifths:")
    for a, b in [("E2", "E2b"), ("E2", "E1"), ("E3", "E2")]:
        L.append(f"  {a} - {b}: {diff(a, b, b_len)}")
    L.append(f"\nE2 refitted on all units (C = {gm.best_params_['logisticregression__C']:g}, "
             f"{len(coef)} words): highest weights")
    L.append("  superstar: " + ", ".join(f"{w} {v:+.2f}" for w, v in zip(top_sup.word, top_sup.weight)))
    L.append("  role:      " + ", ".join(f"{w} {v:+.2f}" for w, v in zip(top_role.word, top_role.weight)))
    L.append(f"  overlap with Fightin' Words top 20: superstar {len(fw_sup & set(top_sup.word))}/20 "
             f"({', '.join(sorted(fw_sup & set(top_sup.word)))}); role {len(fw_role & set(top_role.word))}/20 "
             f"({', '.join(sorted(fw_role & set(top_role.word)))})")
    pr = coef[coef.word.isin(PRONOUNS)].sort_values("weight", ascending=False)
    L.append("  I/we words: " + ", ".join(f"{w} {v:+.2f} (rank {int((coef.weight.abs() > abs(v)).sum()) + 1})"
                                          for w, v in zip(pr.word, pr.weight)))
    txt = "\n".join(L)
    (DATA / "classifier_results.txt").write_text(txt, encoding="utf-8")
    print(txt)
    figure(r)
    print(f"done in {time.time() - t0:.0f} s")


def figure(r):
    """Seed-0 AUC with player-bootstrap 95% CI: all units (filled) and within length fifths (hollow)."""
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    order = ["B1", "B2", "E1", "E2b", "E2", "E3"]
    r = r.set_index("model").loc[order]
    ypos = np.arange(len(order))[::-1].astype(float)
    ax.axvline(0.5, color="#888888", lw=1, ls="--", zorder=1)
    blue = "#2a78d6"
    ax.hlines(ypos + 0.15, r.lo, r.hi, color=blue, lw=2, zorder=2)
    ax.plot(r.auc_seed0, ypos + 0.15, "o", color=blue, ms=8, mec="white", mew=2, zorder=3, label="All units")
    ax.hlines(ypos - 0.15, r.len_lo, r.len_hi, color=blue, lw=1.2, alpha=0.6, zorder=2)
    ax.plot(r.auc_within_length, ypos - 0.15, "o", mfc="white", mec=blue, mew=1.8, ms=7, zorder=3,
            label="Within length fifths (same-length units)")
    for yy, (_, x) in zip(ypos, r.iterrows()):
        ax.text(max(x.hi, x.len_hi) + 0.008, yy, f"{x.auc_seed0:.2f} / {x.auc_within_length:.2f}", va="center",
                fontsize=8.5, color="#333333")
    ax.set_yticks(ypos, [f"{k}  {MODELS[k]}" for k in order])
    ax.set_xlim(0.45, 0.89)
    ax.set_ylim(-0.6, len(order) + 0.3)
    ax.set_xlabel("ROC AUC on held-out players (dashed line = chance, 0.5)")
    ax.set_title("Telling a superstar's press conference from a role player's", fontsize=11)
    ax.legend(loc="upper left", bbox_to_anchor=(0.13, 1.0), fontsize=8, frameon=False, ncol=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color="#e6e6e6", lw=0.8, zorder=0)
    fig.tight_layout()
    fig.savefig(FIG / "classifiers.png", dpi=200)


if __name__ == "__main__":
    main()
